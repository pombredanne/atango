# -*- coding: utf-8 -*-
import os
import re
from lib import app, config, regex
from lib.dialogue import response

re_screen_name = re.compile('@[\w]+[ 　]*')
re_atango = re.compile("[ぁあ]単語((ちゃん)|(先輩))")


class Reply(app.App):

    def __init__(self, verbose=False, debug=False):
        self.cfg = config.read('atango.json')['Reply']
        cfg_dir = config.cfgdir()
        self.replied_id_file = os.path.join(cfg_dir, 'latest_replied.txt')
        self.res_gen = response.ResponseGenerator(verbose, debug)
        super(Reply, self).__init__(verbose, debug)

    def get_latest_replied_id(self):
        if not os.path.exists(self.replied_id_file):
            return 0
        with open(self.replied_id_file, 'r') as fd:
            return int(fd.readlines()[0].rstrip())

    def update_latest_replied_id(self, reply_id):
        with open(self.replied_id_file, 'w') as fd:
            fd.write(str(reply_id))

    def is_valid_mention(self, mention):

        def is_ng_screen_name(screen_name):
            return screen_name in self.cfg['NG_SCREEN_NAME']

        def is_ng_tweet(text):
            return any(word in text for word in self.cfg['NG_WORDS'])

        if (mention['id'] <= self.get_latest_replied_id() or
           is_ng_screen_name(mention['user']['screen_name']) or
           is_ng_tweet(mention['text'])):
            return False
        return True

    def normalize(self, text):
        text = re_screen_name.sub('', text)
        text = re_atango.sub('貴殿', text)
        text = regex.re_url.sub('', text)
        text = text.strip()
        return text

    def run(self, twitter_api, count=10):
        mentions = twitter_api.api.statuses.mentions_timeline(count=count)
        for mention in mentions[::-1]:
            text = self.normalize(mention['text'])
            screen_name = mention['user']['screen_name']
            name = mention['user']['name']
            if not self.is_valid_mention(mention):
                continue
            message = '@%s ' % screen_name
            message += self.res_gen.respond(text, screen_name, name)
            yield message, mention['id']
            self.update_latest_replied_id(mention['id'])

if __name__ == '__main__':
    r = Reply()
    r.run()
