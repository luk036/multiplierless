from .interval import interval
from .point import point


class rectangle(point):
    def __init__(self, x: interval, y: interval):
        """[summary]

        Args:
            x (interval): [description]
            y (interval): [description]
        """
        point.__init__(self, x, y)

    @property
    def lower(self):
        """[summary]

        Returns:
            [type]: [description]
        """
        return point(self.x.lower, self.y.lower)

    @property
    def upper(self):
        """[summary]

        Returns:
            [type]: [description]
        """
        return point(self.x.upper, self.y.upper)

    def copy(self):
        """[summary]

        Returns:
            [type]: [description]
        """
        return rectangle(self.x, self.y)

    # def __eq__(self, rhs) -> bool:
    #     return self.x == rhs.x and self.y == rhs.y

    def flip(self):
        """[summary]

        Returns:
            [type]: [description]
        """
        return rectangle(self.y, self.x)

    # `a` can be point, vsegment, hsegment, or rectangle
    def contains(self, a) -> bool:
        """[summary]

        Args:
            a ([type]): [description]

        Returns:
            bool: [description]
        """
        return self.x.contains(a.x) and self.y.contains(a.y)

    def area(self):
        """[summary]

        Returns:
            [type]: [description]
        """
        return self.x.len() * self.y.len()


class vsegment(point):
    def __init__(self, x, y):
        """[summary]

        Args:
            x ([type]): [description]
            y ([type]): [description]
        """
        point.__init__(self, x, y)

    def copy(self):
        """[summary]

        Returns:
            [type]: [description]
        """
        return vsegment(self.x, self.y)

    # `a` can be point or vsegment
    def contains(self, a) -> bool:
        """[summary]

        Args:
            a ([type]): [description]

        Returns:
            bool: [description]
        """
        return self.x == a.x and self.y.contains(a.y)

    def flip(self):
        """[summary]

        Returns:
            [type]: [description]
        """
        return hsegment(self.y, self.x)


class hsegment(point):
    def __init__(self, x, y):
        """[summary]

        Args:
            x ([type]): [description]
            y ([type]): [description]
        """
        point.__init__(self, x, y)

    def copy(self):
        """[summary]

        Returns:
            [type]: [description]
        """
        return hsegment(self.x, self.y)

    # `a` can be point or hsegment
    def contains(self, a) -> bool:
        """[summary]

        Args:
            a ([type]): [description]

        Returns:
            bool: [description]
        """
        return self.y == a.y and self.x.contains(a.x)

    def flip(self):
        """[summary]

        Returns:
            [type]: [description]
        """
        return vsegment(self.y, self.x)
