import ConfigParser

from event import Matcher, TrueMatcher

# State to return if the event does not match any feed matcher
SKIP_EVENT = 'PASS'


class FeedProcessor(object):

    def setup(self, id, config):
        self.id = id
        try:
            feed_config = open(config['feed_config'])
            config_parser = ConfigParser.SafeConfigParser()
            config_parser.optionxform = str  # case sensitive
            config_parser.readfp(feed_config)
            self.feeds = [dict(config_parser.items(section)) for section in config_parser.sections()]
        except (IOError, ConfigParser.Error), e:
            import sys
            sys.exit(e)

    def process(self, event):
        for feed in self.feeds:
            feed = feed.copy()
            if 'matcher' in feed:
                # Remove matcher from config since its a reserved word
                matcher = Matcher(feed.pop('matcher'))
            else:
                # Process every event
                matcher = TrueMatcher()
            if matcher.matches(event):
                self.process_event(event, feed, matcher.get_match_groups())
        return event

    def process_event(self, event, feed, matched_groups):
        update = {}
        for key, value in feed.iteritems():
            if value.startswith('$') and value[1:] in matched_groups:
                update[key] = matched_groups[value[1:]]
        try:
            event['feed'].update(update)
        except AttributeError:
            event['feed'] = update
        return event
