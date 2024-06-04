import sqlite3
import math

class sqlite():
    def __init__(self, file='sqlite.db'):
        self.file=file
    def __enter__(self):
        self.conn = sqlite3.connect(self.file)
        self.conn.row_factory = sqlite3.Row
        return self.conn.cursor()
    def __exit__(self, type, value, traceback):
        self.conn.commit()
        self.conn.close()

def xp_for_next_level(current_level):
    """
    Returns the xp required to get to the next level from a given level (`level`). If you are on level 1, this function returns
    how much xp you need to get to level 2.
    """
    # the formula is 50 + (x*2)^1.3
    return math.ceil(50 + (current_level*2)**1.3)