import requests
import datetime
from django.core.cache import cache
from redditology.models import Post, Snapshot, PostSnapshot, Author, Subreddit, Domain
from requests.exceptions import RequestException
from celery.task import task, periodic_task
from datetime import timedelta
from celery.utils.log import get_task_logger
from django.utils.timezone import utc

logger = get_task_logger(__name__)

url = 'http://www.reddit.com/.json?limit=100'
headers = {
	'User-Agent': 'redditology_post_fetcher'
}

fetch_period = 10

@periodic_task(run_every = timedelta(seconds=fetch_period))
def fetch_posts():
	"""Fetch Posts

	Get the current top 100 posts on the reddit homepage. Saves the listing of raw un-parsed posts into the cache.
	"""

	try:
		# Make request
		data = requests.get(url=url, headers=headers)
	except RequestException:
		# Catch timeout
		logger.error('Request timed out')
		return

	# Check for data existence
	if not data.json:
		logger.error('No data recieved')
		return

	# Check for correct data type
	if not data.json['kind'] == 'Listing':
		logger.error('Wrong data type recieved')
		return

	logger.info('Fetched current listing')

	# Create snapshot
	s = Snapshot()
	s.save()

	# Contruct packet
	listing = data.json['data']['children']
	listing_cache_key = 'listing_' + str(hash(str(listing)))
	cache.set(listing_cache_key, listing)

	# Send parsing task
	parse_posts.delay(listing_cache_key, s.id)

	
@task
def parse_posts(listing_cache_key, snapshot_id):
	"""Parse Posts

	Wraps individual posts from the listing in the PostParser and sends individual database saving tasks.
	"""

	# Get listing
	listing = cache.get(listing_cache_key, None)

	# Check existence
	if not listing:
		logger.error('Listing not in cache')
		return

	# Consume listing
	cache.delete(listing_cache_key)
	logger.info('Listing ' + listing_cache_key + ' consumed')

	# Parse and send tasks
	for idx, post in enumerate(listing):
		# Check for correct data type
		if not post['kind'] == 't3':
			logger.error('Data type not t3')
			continue
		
		# Correct rank offset
		rank = idx + 1
		# Create parsed post
		parsed_post = PostParser(post, rank)
		cache_key = 'parsed_post_' + str(parsed_post.id) + '_' + str(hash(parsed_post))
		cache.set(cache_key, parsed_post)
		process_post.delay(cache_key, snapshot_id)


@task
def process_post(parsed_post_cache_key, snapshot_id):
	"""Process Posts

	Saves or Updates posts in the database.
	"""

	# Get parsed post from cache
	parsed_post = cache.get(parsed_post_cache_key, None)

	# Check for existence
	if not parsed_post:
		logger.error('Parsed post not in cache')
		return

	# consume post
	cache.delete(parsed_post_cache_key)

	# Get or create post
	try:
		post = Post.objects.get(id=parsed_post.id)
		if parsed_post.edited == True:
			post.title = parsed_post.title
			post.url = parsed_post.url
			post.save()

	except Post.DoesNotExist:
		# Get or create domain
		try:
			domain = Domain.objects.get(name=parsed_post.domain)
		except Domain.DoesNotExist:
			domain = Domain(name=parsed_post.domain)
			domain.save()

		# Get or create author
		try:
			author = Author.objects.get(name=parsed_post.author)
		except Author.DoesNotExist:
			author = Author(name=parsed_post.author)
			author.save()

		# Get or create subreddit
		try:
			subreddit = Subreddit.objects.get(name=parsed_post.subreddit)
		except Subreddit.DoesNotExist:
			subreddit = Subreddit(name=parsed_post.subreddit)
			subreddit.save()

		post = Post(
			id = parsed_post.id,
			title = parsed_post.title,
			url = parsed_post.url,
			over_18 = parsed_post.over_18,
			created_on_reddit = parsed_post.created_on,
			author = author,
			domain = domain,
			subreddit = subreddit
		)
		post.save()

	snapshot = Snapshot.objects.get(id=snapshot_id)

	post_snapshot = PostSnapshot(
		snapshot = snapshot,
		post = post,
		up_votes = parsed_post.up_votes,
		down_votes = parsed_post.down_votes,
		rank = parsed_post.rank,
		num_comments = parsed_post.num_comments
	)
	post_snapshot.save()



class PostParser(object):

	def __init__(self, raw_post, rank):
		self.post = raw_post['data']
		self.rank = rank

	@property
	def title(self):
		return self.post['title']

	@property
	def created_on(self):
		return datetime.datetime.utcfromtimestamp(self.post['created_utc']).replace(tzinfo=utc)

	@property
	def author(self):
		return self.post['author']

	@property
	def over_18(self):
		return self.post['over_18']

	@property
	def id(self):
		return self.post['id']

	@property
	def num_comments(self):
		return self.post['num_comments']

	@property
	def score(self):
		return self.post['score']

	@property
	def up_votes(self):
		return self.post['ups']

	@property
	def down_votes(self):
		return self.post['downs']

	@property
	def domain(self):
		return self.post['domain']
	
	@property
	def url(self):
		return self.post['url']

	@property
	def edited(self):
		return self.post['edited']

	@property
	def subreddit(self):
		return self.post['subreddit']