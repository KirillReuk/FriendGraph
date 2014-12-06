import os
import json
import vk_auth, vk_api
import networkx as nx
import matplotlib.pyplot as plt

target_id = 24448927
debug_mode = False
friends_cache = 'friends.json'
result_dump = 'result.txt'
min_clique_size = 4
clique_ratio = 0.4

class VKApi(object):
	def __init__(self, client_id, scope):
		self.client_id = client_id
		self.scope = scope

		self.token = None
		self.user_id = None

	def ensure_login(self):
		if self.token is None or self.user_id is None:
			self.token, self.user_id = vk_auth.auth(client_id=self.client_id, scope=self.scope)

	def get_name(self, user_id):
		#if debug_mode and os.path.exists(friends_cache):
		#	return load_json(friends_cache)

		self.ensure_login()

		params = {'uid': (self.user_id if user_id is None else user_id)}
		s = vk_api.call_api('users.get', params, self.token)[:]  # The first item is the length

		if debug_mode:
			save_json(friends_cache, s)

		return s
	
	def get_friends(self, user_id=target_id):
		#if debug_mode and os.path.exists(friends_cache):
		#	return load_json(friends_cache)

		self.ensure_login()

		params = {'uid': (self.user_id if user_id is None else user_id)}
		friends = vk_api.call_api('friends.get', params, self.token)[1:]  # The first item is the length

		if debug_mode:
			save_json(friends_cache, friends)

		return friends

	def get_mutual_friends(self, user_id1, user_id2=target_id):
		if debug_mode and os.path.exists(friends_cache):
			return load_json(friends_cache)

		self.ensure_login()

		params = {'target_uid': user_id1, 'source_uid': (self.user_id if user_id2 is None else user_id2)}
		friends = vk_api.call_api('friends.getMutual', params, self.token)  # The first item is the length
		if isinstance(friends, str):
			friends = friends[1:]
			
		if debug_mode:
			save_json(friends_cache, friends)

		return friends
	
	def get_clique_paint(self, G, friends_list):
		H = G.copy()
		color = 1
		color_list = dict(zip(friends_list, friends_list))
		for i in color_list:
			color_list[i] = 1;
		while True:
			color = color + 1
			clique_list = list(nx.algorithms.clique.find_cliques(H))
			max_clique = max(enumerate(clique_list), key = lambda tup: len(tup[1]))[1]
			max_clique_boundary = nx.algorithms.boundary.node_boundary(H, max_clique)
			max_clique_expanded = max_clique[:]
			if len(max_clique_expanded)<min_clique_size:
				break
			for i in max_clique_boundary:
				if len(set(nx.algorithms.boundary.node_boundary(H, [i])).intersection(max_clique))>(len(max_clique)*clique_ratio):
					max_clique_expanded.extend([i])
			for i in max_clique_expanded:
				print(self.get_name(i))
				H.remove_node(i)
				color_list[i] = color
			print('\n')
		
		return color_list

	
def main():
	vk = VKApi(
		client_id='4403869',
		scope=['friends']
		)
	friends_list = vk.get_friends()
	G=nx.Graph()
	G.add_nodes_from(friends_list)
	for i in friends_list:
		print(i)
		try:
			friends_friends_list = vk.get_mutual_friends(i)
		except KeyError:
			continue
		for j in friends_friends_list:
			G.add_edge(i, j)
	print(friends_list)
	
	color_list = vk.get_clique_paint(G, friends_list)			
			
	nx.draw_networkx(G, node_color=color_list.values(), font_color='white', font_size=8)
	#nx.draw_spring(G,node_color='r')
	plt.axis('off')
	plt.tight_layout()
	plt.xlim(-0.05,1.05)
	plt.ylim(-0.05,1.05)
	plt.show()
	
main()
