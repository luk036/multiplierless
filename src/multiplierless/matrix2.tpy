from .vector2 import vector2


class matrix2(vector2):
    def __init__(self, x: vector2, y: vector2):
        """[summary]

        Args:
            x ([type]): [description]
            y ([type]): [description]
        """
        vector2.__init__(self, x, y)

    def copy(self):
        """[summary]

        Returns:
            [type]: [description]
        """
        return matrix2(self._x, self._y)

    def mdot(self, rhs: vector2):
        """[summary]

        Args:
            rhs ([type]): [description]

        Returns:
            [type]: [description]
        """
        return vector2(self._x.dot(rhs), self._y.dot(rhs))

    def det(self):
        """[summary]

        Args:
            rhs ([type]): [description]

        Returns:
            [type]: [description]
        """
        a11, a12 = self.x.x, self.x.y
        a21, a22 = self.y.x, self.y.y
        return a11 * a22 - a12 * a21

    def __neg__(self):
        """[summary]

        Returns:
            [type]: [description]
        """
        return matrix2(-self.x, -self.y)

    def __iadd__(self, rhs):
        """[summary]

        Args:
            rhs ([type]): [description]

        Returns:
            [type]: [description]
        """
        self._x += rhs.x
        self._y += rhs.y
        return self

    def __add__(self, rhs):
        """[summary]

        Args:
            rhs ([type]): [description]

        Returns:
            [type]: [description]
        """
        return matrix2(self.x + rhs.x, self.y + rhs.y)

    def __isub__(self, rhs):
        """[summary]

        Args:
            rhs ([type]): [description]

        Returns:
            [type]: [description]
        """
        self._x -= rhs.x
        self._y -= rhs.y
        return self

    def __sub__(self, rhs):
        """[summary]

        Args:
            rhs ([type]): [description]

        Returns:
            [type]: [description]
        """
        return matrix2(self.x - rhs.x, self.y - rhs.y)

    def __imul__(self, alpha):
        """[summary]

        Args:
            alpha ([type]): [description]

        Returns:
            [type]: [description]
        """
        self._x *= alpha
        self._y *= alpha
        return self

    def __mul__(self, alpha):
        """[summary]

        Args:
            alpha ([type]): [description]

        Returns:
            [type]: [description]
        """
        return matrix2(self.x * alpha, self.y * alpha)

    def __itruediv__(self, alpha):
        """[summary]

        Args:
            alpha ([type]): [description]

        Returns:
            [type]: [description]
        """
        self._x /= alpha
        self._y /= alpha
        return self

    def __truediv__(self, alpha):
        """[summary]

        Args:
            alpha ([type]): [description]

        Returns:
            [type]: [description]
        """
        return matrix2(self.x / alpha, self.y / alpha)
