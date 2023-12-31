import requests
import json
from bs4 import BeautifulSoup
from flask_restful import reqparse
from flask import Blueprint, send_from_directory
from requests.utils import requote_uri
from config import ApiPath, UPLOAD_FOLDER
from utils.lru_cache import timed_lru_cache
from utils.messages import messages
from settings import headers
from utils.plyr import PlyrSource

ModuleTitle = "Anihide"
Moduleid = 'anihide'
ModulePath = Moduleid+'/'
ModuleSiteLink = 'http://anihidex.org/'
hentai = True
Module = Blueprint(ModulePath, __name__)
@Module.route(ApiPath+ModulePath,  methods = ['post'])
def Page():
	parser = reqparse.RequestParser()
	parser.add_argument("page")
	params = parser.parse_args()
	data = GetPage(params.get('page'))
	if data.get('status')!=200:
		return data, data.get('status')
	return json.dumps(data), data.get('status')
@Module.route(ApiPath+ModulePath+'genre',  methods = ['post'])
def GenreRequest():
	parser = reqparse.RequestParser()
	parser.add_argument("genre")
	parser.add_argument("page")
	params = parser.parse_args()
	genre = params.get('genre')
	if not genre:
		return "Не передан параметр genre", 400
	genre = requote_uri(genre)
	genres = GetGenres()
	for key, val in genres.items():
		for item in val['links']:
			if item[1].lower()==genre.lower():
				genre_data = GetGenre(f"/f/{val.get('prelink')}={item[1]}/sort=date/order=desc/", params.get('page'))
				if genre_data.get('data'):
					genre_data['data']['genre_name']=item[0].title()
				return genre_data, genre_data.get('status')
	if genre.isdigit() and len(genre)==4:
		genre_data = GetGenre(f"/f/year={genre}/sort=date/order=desc/", params.get('page'))
		if genre_data.get('status')!=200:
			genre_data['message'] = 'Жанр не найден'
		if genre_data.get('data'):
			genre_data['data']['genre_name']=genre
		return genre_data, genre_data.get('status')
	return {'message': 'Жанр не найден', 'status': 404}, 404
@Module.route(ApiPath+ModulePath+'icon')
def icon():
	return send_from_directory(UPLOAD_FOLDER, 'anihide.svg')
@Module.route(ApiPath+ModulePath+'title',  methods = ['post'])
def TitleRequest():
	parser = reqparse.RequestParser()
	parser.add_argument("id")
	params = parser.parse_args()
	id = params.get('id')
	if not id:
		return {"message":messages['no_param'].format('id'),'status': 400}
	title = GetTitleById(id)
	return title, title.get('status')

def getId(url):
	if url:
		return url.split('/')[-1].split('.')[0]
@timed_lru_cache(60*10)
def GetGenre(GenreUrl, page=None):
	Url = ModuleSiteLink+GenreUrl
	if page is not None:
		if not page.isdigit():
			return {"message": messages['error_page_number'], 'status': 400}
		Url+=f'/page/{page}/'
	return GetTitles(Url)
@timed_lru_cache(60*10)
def GetPage(page):
	if page and not page.isdigit():
		return {
			'status': 400,
			'message': messages.get('error_page_number'),
		}
	return GetTitles(ModuleSiteLink+(f'/page/{page}' if page else ''))

def GetTitles(Url, html=None):
	if not html:
		response = requests.get(Url, headers=headers)
		response.encoding = 'utf8'
	if html or response:
		# with open('title.html', "w", encoding="utf-8") as f:
		# 	f.write(response.text)
		# 	f.close()
		soup = BeautifulSoup(response.text if not html else html, 'lxml')
		data = soup.select('#dle-content')
		if not data:
			return {
				'status': 500,
				'message': 'Ошибка'
			}
		data = data[0]
		outdata = list()
		titles = data.select('article.card')
		if not titles:
			return {
				'status': 404,
				'message': messages.get(404),
			}
		for title in titles:
			title_info = {}
			# short_head = title.select('.short-head')
			title_block = title.select('.card__title > a')
			if title_block:
				title_text = title_block[0].text.split('/')
				title_info['ru_title'] = ' '.join(title_text[0].split())
				if len(title_text)>1:
					title_info['en_title'] = ' '.join(title_text[1].split())
				title_info['id'] = getId(title_block[0].get('href'))
			desc = title.select('.card__desc')
			if desc:
				card_list = desc[0].select('.card__list > li')
				if card_list:
					blocks = list()
					for i in card_list:
						span = i.select('span')
						if not span:
							continue
						span_text = span[0].text.lower()
						text_after_span = span[0].next_sibling
						if not text_after_span or not text_after_span.split():
							continue
						if 'эпизоды' in span_text:
							title_info['series'] = text_after_span+' эпизод'
						if 'качество' in span_text:
							blocks.append('Качество: '+text_after_span.lower())
						elif text_after_span:
							text_after_span = text_after_span.lower()
							if 'онгоинг' in text_after_span:
								title_info['ongoing'] = True
					title_info['info_blocks'] = blocks			
			poster = title.select('.card__img > img')
			if poster:
				title_info['poster'] = ModuleSiteLink[:-1]+poster[0].get('src')
			outdata.append(title_info)
		pages = data.select('.pagination > .pagination__pages > *')
		return {
			'status': 200,
			'data': {
				'data': outdata,
				'horny': hentai,
				'pages': int(pages[-1].text) if pages else 1,
				'service_title': ModuleTitle,
			},
		}
	else:
		return {
			'status': response.status_code if not html else 404,
			'message': messages.get('not_response'),
		}

@timed_lru_cache(60*60*6)
def GetGenres():
	genres = requests.get(ModuleSiteLink, headers=headers)
	genres.encoding = 'utf8'
	if genres:
		soup_genres = BeautifulSoup(genres.text, 'lxml')
		tags = soup_genres.select('.side-block__content > .nav-col > .nav-menu > li > a')
		if not tags:
			return {
				'status': 500,
				'message': 'Ошибка'
			}
		return {
			'genre': {
				'links': [[i.text, requote_uri(i.get('href').split('/')[-1].split('=')[-1])] for i in tags],
				'prelink': 'j.genres',
				'name': 'Жанр',
			},
		}
@timed_lru_cache(60*60)
def GetTitleById(title_id):
	response = requests.get(ModuleSiteLink+title_id+'.html', headers=headers)
	response.encoding = 'utf8'
	if response:
		soup = BeautifulSoup(response.text, 'lxml')
		dle_content = soup.select('#dle-content')
		if not dle_content:
			return {
				'status': 500,
				'message': messages.get('error_parce')
			}
		# with open('title.html', "w", encoding="utf-8") as f:
		# 	f.write(response.text)
		# 	f.close()
		out = {}
		subcols = dle_content[0].select('article > .page__subcols')
		if not subcols:
			return {
			'status': 404,
			'message': messages.get('not_response'),
		}
		title = soup.find("meta", property="og:title")
		title_text = None
		if title:
			title_text = title.get('content')
		else:
			title = subcols[0].select('.page__header > h1')
			if title:
				title_text = title[0].text
		if title_text:
			title_text = title_text.split('/')
			out['ru_title'] = ' '.join(title_text[0].split())
			if len(title_text)>1:
				out['en_title'] = ' '.join(title_text[1].split())
		poster = subcols[0].select('.page__subcol-side > .pmovie__poster > img')
		if poster:
			out['poster'] = ModuleSiteLink[:-1]+poster[0].get('src')
		desc = dle_content[0].select('article > .page__text')
		if desc:
			out['description'] = desc[0].text
		related = dle_content[0].select('article > section.pmovie__related > .sect__content > a')
		if related:
			related_list = list()
			for i in related:
				related_title = {}
				related_title['id'] = getId(i.get('href'))
				related_poster = i.select('.poster__img > img')
				if related_poster:
					related_title['poster'] = ModuleSiteLink[:-1]+related_poster[0].get('src')
				related_title_block = i.select('.poster__title')
				if related_title_block:
					related_title['ru_title'] = related_title_block[0].text
				related_list.append(related_title)
			if related_list:
				out['related'] = related_list
		subcol_main = subcols[0].select('.page__subcol-main')
		blocks = list()
		if subcol_main:
			year = subcol_main[0].select('.pmovie__year')
			if year:
				year_link = year[0].find('a')
				if year_link:
					year_text = [year_link.text]
					if year_text[0].isdigit():
						year_text*=2
					out['year'] = year_text
			
			pmovie_header = subcol_main[0].select('ul.pmovie__header-list > li > div')
			if pmovie_header:
				for i in pmovie_header:
					block = [i.text]
					next_sibling = i.next_sibling
					if next_sibling:
						block.append(next_sibling.text)
					blocks.append(block)

			pmovie_bottom = subcol_main[0].select('.pmovie__bottom > .card__ratings > .card__rating-ext')
			if pmovie_bottom:
				for i in pmovie_bottom:
					block_title = i.get('data-text')
					if not block_title:
						continue
					block = [block_title]
					block_text = i.findAll(text=True, recursive=False)
					if block_text:
						block.append(block_text[0].text)
					blocks.append(block)
		page_subcol2 = subcols[0].select('ul.page__subcol-side2 > li')
		if page_subcol2:
			for i in page_subcol2:
				spans = i.select('span')
				if len(spans)>1:
					blocks.append([spans[0].text,spans[1].text])
				else:
					div = i.select('div')
					if div:
						block = [div[0].text]
						next_sibling = div[0].next_sibling
						if "Жанр:" == block[0]:
							if next_sibling:
								title_genres = next_sibling.text.split(' / ')
								if title_genres:
									title_genres[0] = ' '.join(title_genres[0].split())
									title_genres[-1] = ' '.join(title_genres[-1].split())
									title_genres_lower = [i.lower() for i in  title_genres]
									genres = GetGenres()
									out_genres = list()
									for key, val in genres.items():
										for item in val['links']:
											if item[0].lower() in title_genres_lower:
												index = title_genres_lower.index(item[0].lower())
												title_genres_lower.pop(index)
												out_genres.append(item)
									if title_genres_lower:
										for i in title_genres_lower:
											out_genres.append([i])
									out['genre'] = out_genres
						else:
							if next_sibling:
								block.append(next_sibling.text)
							blocks.append(block)
		out['blocks'] = blocks
		player = dle_content[0].select('.pmovie__player > .tabs-block__content > script')
		if player:
			urls = player[0].text.split('file:"')[-1].split('"}')[0].split(' or ')
			series = None
			for url in urls:
				response = requests.get(url)
				response.encoding = 'utf8'
				if response:
					response_series = response.json()
					series = list()
					for i in response_series:
						episode=PlyrSource(i.get('file').split(' and ')[-1],i.get('poster'))
						episode['name'] = i.get('title')
						series.append(episode)
					break
			out['series'] = {}
			if series:
				out['series']['direct_link']=False
				out['series']['data'] = series
		# mov_desc = short_item[0].select('.mov-desc')
		# if mov_desc:
		# 	description = mov_desc[0].select('.full-text')
		# 	if description:
		# 		out['description'] = description[0].text
		# 	divs = mov_desc[0].select('* > div')
		# 	if len(divs)>=2:
		# 		screens = divs[2].select('a')
		# 		if screens:
		# 			print([ModuleSiteLink+i.get('href')[1:] for i in screens])
		# player = dle_content[0].select('article > .player-section > .player-box > .reclama > script')
		# print(player)


		# series = dle_content[0].select('.tab_content > .tabs > .series-btn > .s-link')
		# out['series'] = {}
		# if series:
		# 	out_series = list()
		# 	for i in series:
		# 		if 'vip.php' not in i.get('data-src'):
		# 			link = i.get('data-src').split('/')
		# 			if 'hub' in link:
		# 				out_series.append({
		# 					'link':"/"+ModulePath+'video/'+link[link.index('hub')+1]+"/"+i.get('data-src').split('id=')[1],
		# 					'name': i.text,
		# 				})
		# 	if out_series:
		# 		out['series']['data'] = out_series
		# 		first_splited_link = out_series[0]['link'].split('/')
		# 		first = GetVideoById(first_splited_link[-1],first_splited_link[-2])
		# 		if first.get('status')==200:
		# 			first = first.get('data')
					
		# 			first['name'] = out_series[0]['name']
		# 			out['series']['data'][0] = first
		# 		out['series']['direct_link']=False
		# fmright = dle_content[0].select('.fmright')
		# if fmright:
		# 	blocks = list()
		# 	for items_container in fmright[0].select('.flist > .flist-col > .vis'):
		# 		items = items_container.select('* > span')
		# 		value = list()
		# 		if not items:
		# 			continue
		# 		if len(items)==1:
		# 			text_in_tag = items[0].text
		# 			text_after_tag = ' '.join(items[0].next_sibling.split())
		# 			if text_in_tag == "Релиз от:":
		# 				numbs = next(re.finditer(r"\d{4}", text_after_tag), None)
		# 				if numbs:
		# 					numb = numbs.group(0)
		# 					genres = GetGenres()
		# 					for key, val in genres.items():
		# 						for item in val['links']:
		# 							if item[1]==str(numb):
		# 								out['year'] = [numb]*2
		# 					if not out.get('year'):
		# 						out['year'] = [numb]
		# 					continue
		# 			elif text_in_tag == 'Эпизоды:':
		# 				out['series']['info'] = [text_after_tag]
		# 				continue

		# 			value.append(text_in_tag)
		# 			value.append([text_after_tag])
		# 		else:
		# 			text = list()
		# 			tag_name = items.pop(0).text
		# 			if tag_name == "Жанры:":
		# 				items.pop(0)
		# 			value.append(tag_name)
		# 			for tag in items:
		# 				if value[0] == "Жанры:":
		# 					a = tag.select('a')
		# 					if a:
		# 						text.append([a[0].text, a[0].get('href').split('/')[-2]])
		# 					else:
		# 						text.append([tag.text])
		# 				else:
		# 					text_in_tag = tag.text
		# 					if text_in_tag:
		# 						text.append(text_in_tag)
		# 			value.append(text)
		# 		if value[0] == "Жанры:":
		# 			out['genre'] =  value[1]
		# 			continue
		# 		blocks.append(value)
		# 	out['blocks'] = blocks
		# fdownloads = dle_content[0].select('#fdownloads')
		# if fdownloads:
		# 	frelated = fdownloads[0].select('.frelated .tc-item')
		# 	if frelated:
		# 		related_list = list()
		# 		for i in frelated:
		# 			related_data = {}
		# 			related_poster = i.select('img')
		# 			if related_poster:
		# 				related_poster = related_poster[0].get('src').replace('/thumbs/', '/')
		# 				related_data['poster'] = (related_poster if related_poster.startswith('//') else HentaizLink+related_poster)
		# 			related_title = i.select('.tc-title')
		# 			if related_title:
		# 				related_data['ru_title'] = related_title[0].text
		# 			related_data['id'] = i.get('href').split('/')[-1].split('.')[0]
		# 			related_list.append(related_data)
		# 		if related_list:
		# 			out['related'] = related_list
		out['service_title'] = ModuleTitle
		out['horny'] = hentai
		return {
			'status':200,
			'data': out,
		}
	else:
		return {
			'status': response.status_code,
			'message': messages.get('not_response'),
		}