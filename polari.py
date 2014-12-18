#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2014, Cristian García <cristian99garcia@gmail.com>
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

from gettext import gettext as _

from gi.repository import Gtk

from sugar3.activity import activity
from sugar3.graphics.toolbutton import ToolButton
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import _create_activity_icon as ActivityIcon

from widgets import AddChannelBox
from widgets import ChannelsView
from widgets import ChatView
from widgets import Canvas

from irc.client import Client


class PolariActivity(activity.Activity):

    def __init__(self, handle):
        activity.Activity.__init__(self, handle)

        self.max_characters = 4096
        self.rooms = {}
        self.actual_room = None

        self._canvas = Canvas()
        self._channels_view = self._canvas.channels_box

        self.set_size_request(500, 300)
        self.make_toolbar()

        self._channels_view.connect('channel-selected', self.channel_changed)
        self._channels_view.connect('channel-removed', self.remove_channel)
        self._canvas.pack_start(self._channels_view, False, False, 1)

        self.set_canvas(self._canvas)
        self.show_all()

        self.add_channel()

    def remove_channel(self, widget, host, channel):
        room = self.rooms[host + '@' + channel]
        room['client'].close()
        self._canvas.remove(room['chat-view'])
        room['chat-view'].destroy()

        _dict = {}

        for room, values in self.rooms.items():
            if room != host + '@' + channel:
                _dict[room] = values

        self.rooms = _dict

    def channel_changed(self, widget, host, channel):
        channel = channel[1:] if channel.startswith('#') else channel
        self.actual_room = host + '@' + channel
        self.set_chat_view(self.rooms[self.actual_room]['chat-view'])

    def make_toolbar(self):
        def make_separator(expand=False, size=0):
            separator = Gtk.SeparatorToolItem()
            separator.set_size_request(size, -1)
            if expand:
                separator.set_expand(True)

            if expand or size:
                separator.props.draw = False

            return separator

        toolbar_box = ToolbarBox()
        toolbar = toolbar_box.toolbar
        activity_button = ToolButton()
        button_add = ToolButton(Gtk.STOCK_ADD)
        self.entry_nick = Gtk.Entry()
        stop_button = ToolButton('activity-stop')

        activity_button.set_icon_widget(ActivityIcon(None))
        button_add.set_tooltip(_('Add channel'))
        stop_button.connect('clicked', self._exit)
        stop_button.props.accelerator = '<Ctrl>Q'

        button_add.connect('clicked', self.add_channel)

        toolbar.insert(activity_button, -1)
        toolbar.insert(make_separator(size=30), -1)
        toolbar.insert(button_add, -1)
        toolbar.insert(make_separator(expand=True), -1)
        toolbar.insert(stop_button, -1)
        self.set_toolbar_box(toolbar_box)

    def set_nickname(self, chat_view, nickname, room):
        if room['client'].connected:
            room['client'].set_nickname(nickname)

        else:
            room['client'].nickname = nickname

    def add_channel(self, widget=None):
        if not self.actual_room:
            nick = None
            host = None
            channel = None
            port = None

        else:
            nick = self.rooms[self.actual_room]['nickname']
            host = self.rooms[self.actual_room]['host']
            channel = self.rooms[self.actual_room]['channel']
            port = self.rooms[self.actual_room]['port']

        box = AddChannelBox(nick, host, channel, port)

        box.connect('new-channel', self.new_channel)
        box.connect('new-channel', self._canvas.set_originals_boxes)
        box.connect('cancel', self._canvas.set_originals_boxes)

        self._canvas.set_canvas(box)
        self.show_all()

    def new_channel(self, widget, nick, host, channel, port):
        self.create_new_room(host, channel, nick, port)

    def create_new_room(self, host, channel, nick, port):
        if channel.startswith('#'):
            channel = channel[1:]

        room = {}
        room['host'] = host
        room['channel'] = channel
        room['nickname'] = nick
        room['port'] = port
        room['chat-view'] = ChatView()
        room['max-characters'] = self.max_characters
        room['entry-speak'] = room['chat-view'].entry
        room['entry-nick'] = room['chat-view'].nicker
        room['client'] = Client(room)
        room['client'].entry = room['entry-speak']
        room['client'].nicker = room['entry-nick']

        self.actual_room = host + '@' + channel
        self.rooms[self.actual_room] = room

        room['chat-view'].connect('nickname-changed', self.set_nickname, room)
        room['entry-speak'].connect('activate', self.send_message, room)
        room['client'].connect('connected', self.client_connected)
        room['client'].connect('connected', self._stop_last_item_child, room)

        room['chat-view'].set_user(room['nickname'])
        room['chat-view'].set_client(room['client'])
        self.set_chat_view(room['chat-view'])

        self._channels_view.add_channel(channel, host)

    def _stop_last_item_child(self, client, room):
        vbox = self._channels_view.sections[room['host']]
        for item in vbox:
            if item.host == room['host']:
                item.stop_last_widget()

    def client_connected(self, client):
        client.entry.set_sensitive(True)
        client.nicker.set_sensitive(True)

    def set_chat_view(self, view):
        self._canvas.set_chat_view(view)
        self.show_all()

    def send_message(self, widget, room):
        room['client'].say(widget.get_text())

    def _exit(self, *args):
        for room in self.rooms:
            client = self.rooms[room]['client']
            client.close()

        self.close()
