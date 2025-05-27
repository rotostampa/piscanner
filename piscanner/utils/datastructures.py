class data(dict):
    def __getattr__(self, attr):
        try:
            return self.__getitem__(attr)
        except KeyError:
            raise AttributeError(
                "'{}' object has no attribute '{}'".format(
                    self.__class__.__name__, attr
                )
            )

    def __setattr__(self, attr, value):
        return self.__setitem__(attr, value)

    def __delattr__(self, attr):
        return self.__delattr__(attr)
