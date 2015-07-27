#!/usr/bin/env python3

import asyncio
import humphrey
import json
import pathlib
import urllib.error
import urllib.parse
import urllib.request

CHAN_ID_TO_NAME = [
    'Rainwave network',
    'Game channel',
    'OCR channel',
    'Covers channel',
    'Chiptune channel',
    'All channel'
]

IRC_CHAN_TO_ID = {
    '#game.rainwave.cc': 1,
    '#ocr.rainwave.cc': 2,
    '#covers.rainwave.cc': 3,
    '#chiptune.rainwave.cc': 4,
    '#all.rainwave.cc': 5
}


def get_info(bot):
    url = 'http://rainwave.cc/api4/info_all'
    args = {'sid': 1}
    data = urllib.parse.urlencode(args).encode()
    try:
        response = urllib.request.urlopen(url, data=data)
    except urllib.error.URLError as e:
        bot.log('** {}'.format(e))
        return None
    if response.status == 200:
        body = response.read().decode()
        return json.loads(body)
    return None


def announce(chan_id, bot):
    info = get_info(bot)
    if info is None:
        bot.loop.call_later(30, announce, chan_id, bot)
        return
    chan_info = info['all_stations_info'][str(chan_id)]
    song = None
    try:
        song = '{album} // {title}'.format(**chan_info)
    except TypeError:
        bot.loop.call_later(30, announce, chan_id, bot)
    last = bot.c.get('rw:{}'.format(chan_id))
    if song == last:
        bot.loop.call_later(30, announce, chan_id, bot)
        return
    chan_name = CHAN_ID_TO_NAME[chan_id]
    irc_channel = bot.c.get('irc:channel:{}'.format(chan_id))
    m = 'Now playing on the {}: {}'.format(chan_name, song)
    bot.send_privmsg(irc_channel, m)
    bot.c['rw:{}'.format(chan_id)] = song
    bot.loop.call_later(30, announce, chan_id, bot)


def main():
    config_file = pathlib.Path(__file__).resolve().with_name('_config.json')
    irc = humphrey.IRCClient(config_file)
    irc.c.pretty = True
    irc.debug = True

    @irc.ee.on('366')
    def start_announcing(message, bot):
        tokens = message.split()
        irc_channel = tokens[3]
        chan_id = IRC_CHAN_TO_ID[irc_channel]
        announce(chan_id, bot)

    @irc.ee.on('376')
    def on_rpl_endofmotd(_, bot):
        for chan_id in range(1, 6):
            channel = bot.c.get('irc:channel:{}'.format(chan_id))
            bot.out('JOIN {}'.format(channel))

    loop = asyncio.get_event_loop()
    host = irc.c.get('irc:host')
    port = irc.c.get('irc:port')
    while True:
        coro = loop.create_connection(irc, host, port)
        loop.run_until_complete(coro)
        loop.run_forever()

if __name__ == '__main__':
    main()
