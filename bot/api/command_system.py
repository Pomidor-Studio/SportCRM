from typing import Tuple, Optional, List


class InvalidCommand:
    pass


class Command:
    description: str = ...
    keys: List[str] = ...

    def __init__(self) -> None:
        super().__init__()

    def damerau_levenshtein_distance(self, s1: str, s2: str):
       d = {}
       lenstr1 = len(s1)
       lenstr2 = len(s2)
       for i in range(-1, lenstr1 + 1):
           d[(i, -1)] = i + 1
       for j in range(-1, lenstr2 + 1):
           d[(-1, j)] = j + 1
       for i in range(lenstr1):
           for j in range(lenstr2):
               if s1[i] == s2[j]:
                   cost = 0
               else:
                   cost = 1
               d[(i, j)] = min(
                   d[(i - 1, j)] + 1,  # deletion
                   d[(i, j - 1)] + 1,  # insertion
                   d[(i - 1, j - 1)] + cost,  # substitution
               )
               if i and j and s1[i] == s2[j - 1] and s1[i - 1] == s2[j]:
                   d[(i, j)] = min(d[(i, j)], d[i - 2, j - 2] + cost)  # transposition
       return d[lenstr1 - 1, lenstr2 - 1]

    def is_good_request(self, user_message: str):
        for key in self.keys:
            d = self.damerau_levenshtein_distance(user_message, key)
            if d == 0 or d < len(user_message) * 0.4:
                return True
        return False

    def handle_user_message(self, user_message: str, user_id: int):
        if self.is_good_request(user_message):
            return self.process(user_id)
        else:
            raise InvalidCommand()

    def process(self) -> Tuple[str, Optional[str]]:
        raise NotImplementedError('Define process method')
