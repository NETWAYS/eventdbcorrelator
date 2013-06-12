from receptors.abstract_receptor import AbstractReceptor


class DummyReceptor(AbstractReceptor):
    """
    Receptor that simply does nothing
    Only needed to ensure that a chain is always existing
    """
    pass