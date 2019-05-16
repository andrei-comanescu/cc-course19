import os
import pickle
from pattern.en import pluralize, singularize

import logging
logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)

try:
    from .templates import TemplateBank, Title
except ImportError:
    from templates import TemplateBank, Title

try:
    from .evaluator import Evaluator
except ImportError:
    from evaluator import Evaluator

try:
    from .wordpicker import WordPicker, AttributeNotFound
except ImportError:
    from wordpicker import WordPicker, AttributeNotFound

class tittlesTitle():
    def __init__(self):
        self.threshold = 0.825
        self.domain = 'word'
        self.folder = os.path.dirname(os.path.realpath(__file__))
        self.evaluator = Evaluator()
        self.wordpicker = WordPicker()
        self.template_bank = TemplateBank(self.evaluator.title_bank)


    def generate(self, *args, **kwargs):
        return self.create("", {}, number_of_artifacts=1)

    def find_words(self, adjectives, activity, location, weather, slots):
        return self.wordpicker.find_pairs(adjectives, activity, location, weather, slots)

    def evaluate(self, title):
        """
        Evaluates given title to [0,1] range. 1 being best possible value.

        Args:
            Title (str) : title to be evaluated.

        Returns:
            Float [0, 1] : How good the title was - high being better.
        """
        return self.evaluator.evaluate(title.split(" "), self.emotion)

    def inject(self, title, word_pair):
        for (i, slot), word in zip(title.slots, word_pair):
            word = word.replace("_", " ").title()
            if slot == 'NOUN':
                title.inject(singularize(word), slot, i)
            elif slot == 'NOUNS':
                title.inject(pluralize(singularize(word)), slot, i)
            else:
                title.inject(word, slot, i)

    def create(self, emotion, word_pairs, number_of_artifacts=10, **kwargs):
        """Create artifacts in the group's domain.

        The given inputs can be parsed and deciphered by the system using any methods available.

        The function should return a list in the form of:

            [
                (artifact1, {"evaluation": 0.76, 'foo': 'bar'}),
                (artifact2, {"evaluation": 0.89, 'foo': 'baz'}),
                # ...
                (artifactn, {"evaluation": 0.29, 'foo': 'bax'})
            ]

        :param str emotion:
            One of "the six basic emotions": anger, disgust, fear, happiness, sadness or surprise.
            The emotion should be perceivable in the output(s).
        :param list word_pairs:
            List of 2-tuples, the word pairs associated with the output(s). The word_pairs are (noun, property) pairings
            where each pair presents a noun and its property which may be visible in the output. (Think of more creative
            ways to present the pairings than literal meaning.)
        :param int number_of_artifacts:
            Number of artifacts returned
        :returns:
            List with *number_of_artifacts* elements. Each element should be (artifact, metadata) pair, where metadata
            should be a dictionary holding at least 'evaluation' keyword with float value.

        """

        self.emotion = emotion

        ret = []

        subsequent_catches = 0

        while len(ret) != number_of_artifacts:
            logger.debug('generate new title')

            adjectives = (list(word_pair[1] for word_pair in word_pairs if word_pair[0] == 'animal'), list(word_pair[1] for word_pair in word_pairs if word_pair[0] == 'human'))
            weather = dict(word_pairs)['weather']
            activity = dict(word_pairs)['activity']
            location = dict(word_pairs)['location']

            template = self.template_bank.random_template()
            title = Title(template)

            try:
                word_pair = self.find_words(adjectives, activity, location, weather, title.slots)
                subsequent_catches = 0
            except AttributeNotFound:
                subsequent_catches += 1
                if subsequent_catches > 20:
                    # Really unlikely case.
                    raise AttributeNotFound("Input attributes cannot be found from Thesaurus Rex.")
                continue

            self.inject(title, word_pair)
            logger.debug('final title: ' + str(title))

            v = self.evaluate(' '.join(title.tokens))
            if v >= self.threshold:
                phenotype = str(title)
                ret.append((phenotype, {"evaluation": v}))
                self.evaluator.add_title(phenotype)
            else:
                logger.debug('evaluation below threshold')

        # Comment out if you want to keep the original titles
        self.evaluator.dump_titles()
        return ret

if __name__ == "__main__":
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    import inputs
    emotion, word_pairs = inputs.get_input(False)
    T = tittlesTitle()
    print('INPUT')
    print('emotion:', emotion)
    for category, word in word_pairs:
        print(category + ': ' + word)
    print('')
    print('OUTPUT')
    for title, meta in T.create(emotion, word_pairs, number_of_artifacts=3):
        print('title:', title)
        print('evaluation:', meta['evaluation'])
        print('')
