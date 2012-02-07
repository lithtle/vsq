#! /usr/bin/python
# -*- coding: utf-8 -*-

class Student:
    def __init__(self, name, id, courage):
        """インスタンス変数の宣言"""
        self.name = name
        self.id = id
        self.courage = courage

    def __str__(self):
        return self.name + "_" + str(self.id) + "_" + self.courage

    def isStudentOf(self, courage):
        if self.courage == courage:
            return True
        else:
            return False

    
if __name__ == "__main__":
    s = Student("satoh", 201411450, "coins")
    print s.isStudentOf("coins")
    print s
    
