#!/usr/bin/env python2
# -*- coding: utf-8 -*-

class Sudoku():
    """Represents the sudoku itself, keeps track of the filling
    and check if moves are legal
    """
    
    def __init__(self):
        self.__game_grid, self.__finished_grid = generate_grid()
        #...
    
    def insert(number, coordinate)
        """Insert number into sudoku
        :param number, int from 1-9
        :param coordinate tuple (x, y)
        :returns tuple (point, finish) 
                 point, int from -1 to 1
                 -1 -> False
                 0 -> already full coord.
                 1 -> True
                 
                 finish, boolean
        """
        if self.__game_grid[coordinate.x][coordinate.y] == '0':
            if check_if_legal(number, coordinate):
                self.__game_grid[coordinate.x][coordinate.y] = number
                point = 1 
            else:
                point = -1
        else:
            point = 0    
            
        return point, check_if_finished()
    
    
    def generate_grid(self):
        """generate a sudoku grid
        :returns tuple (game_grid, finished_grid)
                start_grid, [9][9]
                full_grid, [9][9]
        """
        #...
        pass        
    
    def get_grid(self):
        return self.__game_grid
    
    def check_if_legal(number, coordinate):
        #...
        pass
    
    def check_if_finished():
        return self.__game_grid == self.__finished_grid
