from flask.views import MethodView
from helpers import token_required
from flask import g, request, jsonify, abort, make_response
from app.Models import Post, posts_schema, post_schema, user_schema
from app import app, db
import json
from helpers import slugify, custom_response
from sqlalchemy import desc, asc

APP_URL = app.config.get('APP_URL')

class PostAPI(MethodView):
	def get(self, id=None, slug=None):
		#get param page request
		try:
			page = int(request.args.get('page', 1))
			limit = int(request.args.get('limit', 10))
			orderBy = request.args.get('orderBy')
		except:
			page = 1
			limit =10
			orderBy = None
		#check get id request
		if (not id) and (not slug):
			try:
				#query get data from database 
				# check orderBy
				posts_paginate = Post.query.paginate(page, limit)
				if orderBy:
					arr_orderby = orderBy.split(".")
					if arr_orderby[0] == "desc":
						posts_paginate = Post.query.order_by(desc(arr_orderby[1])).paginate(page, limit)
					if arr_orderby[0] == 'asc':
						posts_paginate = Post.query.order_by(asc(arr_orderby[1])).paginate(page, limit)
				
				posts = posts_paginate.items

				res = {}
				data = []

				posts_data = posts_schema.dump(posts).data
				# get info author
				for index in range(len(posts_data)):
					posts_data[index].update({
						"author": {
							"name": posts[index].author.name,
							"avatar": posts[index].author.avatar
						}
					})
				res.update({
					"data": posts_data
				})

				#paging 
				url_previous = ""
				url_next =  ""
				paging = {}

				if posts_paginate.has_next:
					url_next = APP_URL +"/api/v1/posts?page=" + str((page + 1)) + "&limit="+str(limit)
					paging.update({"next": url_next})
				if posts_paginate.has_prev:
					url_previous = APP_URL +"/api/v1/posts?page=" + str((page - 1)) + "&limit="+str(limit)
					paging.update({"previous": url_previous})

				#response
				res.update({
					"paging": paging,
					"pages": posts_paginate.pages,
					"per_page": page,
					"next_num": posts_paginate.next_num,
					"prev_num": posts_paginate.prev_num,
					"limit": limit
				})
			except Exception as e:
				print(e)
				# "error": e.get_description(),
				res = {
					"data": []
				}
				return jsonify(res)
		else:
			if id:
				post = Post.query.filter_by(id=id).first()

				if not post:
					res = {
						"error": {
							"message": "Unsupported get request. Object with ID " + str(id)+" does not exist"
						}
					}
					# abort(404)
					return jsonify(res), 404
				res = post_schema.dump(post).data
			if slug:
				post = Post.query.filter_by(slug=slug).first()
				author = {
					"name": post.author.name,
					"avatar": post.author.avatar
				}

				if not post:
					res = {
						"error": {
							"message": "Unsupported get request. Object with slug " + str(slug)+" does not exist"
						}
					}
					return jsonify(res), 404
				res = post_schema.dump(post).data

				res['author'] = author
		return make_response(jsonify(res))

	#create post
	@token_required
	def post(self):
		#get data from client
		try:
			data = request.get_json()
			post = Post(
				content = data.get('content'),
				title = data.get('title'),
				thumbnail = data.get('thumbnail'),
				slug = slugify(data.get('title')),
				description = data.get('description'),
				user_id = g.user.id,
				status = data.get('status', 1),
				view_count = 0,
				category_id = data.get('category_id')
			)
			db.session.add(post)
			db.session.commit()

			res = {
				"status": "ok",
				"code": 200,
				"message": "The post was successfully added",
				"post": post_schema.dump(post).data
			}
			return make_response(jsonify(res)), 200
		except Exception as e:
			res = {
				"status": "fail",
				"code": 400,
				"message": "failed",
			}
			return make_response(jsonify(res)), 400
	@token_required
	def delete(self, id):
		# delete a single user
		post = Post.get_one_user(id)
		if not post:
			return custom_response({
				'status': 'fail',
				'message': 'Not found id ' + str(id),
				'method' : 'DELETE'
			}, 400)
		try:
			post.delete()
			return custom_response({
				'status': 'success',
				"message" : "deleted",
				'method' : 'DELETE'
			}, 200)
		except:
			return custom_response({
				'status': 'fail',
				'message': 'Some error occurred. Please try again.',
				'method' : 'DELETE'
			}, 401)

	@token_required
	def put(self, id):
		post = Post.get_one_user(id)
		if not post:
			return custom_response({
				'status': 'fail',
				'message': 'Not found id ' + str(id),
				'method' : 'PUT'
			}, 400)
		# update a single user
		"""
		Update me
		"""
		try:
			data = request.get_json()
			if data.get('content'):
				post.content = data.get('content')
			if data.get('title'):
				post.title = data.get('title')
			if data.get('thumbnail'):
				post.thumbnail = data.get('thumbnail')
			if data.get('description'):
				post.description = data.get('description')
			if data.get('status'):
				post.status = data.get('status')
			if data.get('view_count'):
				post.view_count = data.get('view_count')
			if data.get('category_id'):
				post.category_id = data.get('category_id')
			db.session.add(post)
			db.session.commit()
			return custom_response({
				'status': 'success',
				"message" : "updated",
				"method" : 'PUT',
				"post": post_schema.dump(post).data
			}, 200)
		except:
			return custom_response({
				'status': 'fail',
				'message': 'Some error occurred. Please try again.',
				'method' : 'PUT'
			}, 401)