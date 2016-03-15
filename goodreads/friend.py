'''
Created on Dec 20, 2015

@author: ishaansutaria
'''


class GoodreadFriend():

    def __init__(self, friend_dict):
        self._friend_dict = friend_dict

    @property
    def friend_id(self):
        return self._friend_dict['id']

    @property
    def friend_name(self):
        return self._friend_dict['name']

    @property
    def friend_count(self):
        return self._friend_dict['friends_count']