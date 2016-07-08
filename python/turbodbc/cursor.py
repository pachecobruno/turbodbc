from __future__ import absolute_import

from itertools import islice

from turbodbc_intern import has_result_set, make_row_based_result_set

from .exceptions import translate_exceptions, InterfaceError


class Cursor(object):
    def __init__(self, impl):
        self.impl = impl
        self.result_set = None
        self.rowcount = -1
        self.arraysize = 1

    def __iter__(self):
        return self

    def next(self):
        element = self.fetchone()
        if element is None:
            raise StopIteration
        else:
            return element

    def _assert_valid(self):
        if self.impl is None:
            raise InterfaceError("Cursor already closed")

    def _assert_valid_result_set(self):
        if self.result_set is None:
            raise InterfaceError("No active result set")

    @property
    def description(self):
        info = self.impl.get_result_set_info()
        if len(info) == 0:
            return None
        else:
            return [(c['name'], c['type_code'], None, None, None, None, c['supports_null_values']) for c in info]

    @translate_exceptions
    def execute(self, sql, parameters=None):
        """Execute an SQL query"""
        self._assert_valid()
        self.impl.prepare(sql)
        if parameters:
            # TODO: The list call here is probably inefficient
            # will go once the translation layer is better
            self.impl.add_parameter_set(list(parameters))
        self.impl.execute()
        self.rowcount = self.impl.get_row_count()
        cpp_result_set = self.impl.get_result_set()
        if has_result_set(cpp_result_set):
            self.result_set = make_row_based_result_set(cpp_result_set)
        else:
            self.result_set = None

    @translate_exceptions
    def executemany(self, sql, parameters=None):
        """Execute an SQL query"""
        self._assert_valid()
        self.impl.prepare(sql)

        if parameters:
            for parameter_set in parameters:
                # TODO: The list call here is probably inefficient
                # will go once the translation layer is better
                self.impl.add_parameter_set(list(parameter_set))

        self.impl.execute()
        self.rowcount = self.impl.get_row_count()
        cpp_result_set = self.impl.get_result_set()
        if has_result_set(cpp_result_set):
            self.result_set = make_row_based_result_set(cpp_result_set)
        else:
            self.result_set = None

    @translate_exceptions
    def fetchone(self):
        self._assert_valid_result_set()
        result = self.result_set.fetch_row()
        if len(result) == 0:
            return None 
        else:
            return result  

    @translate_exceptions    
    def fetchall(self):
        return [row for row in self]

    @translate_exceptions    
    def fetchmany(self, size=None):
        if size is None:
            size = self.arraysize
        if (size <= 0):
            raise InterfaceError("Invalid arraysize {} for fetchmany()".format(size))

        return [row for row in islice(self, size)]

    def close(self):
        self.result_set = None
        self.impl = None

    def setinputsizes(self, sizes):
        """
        setinputsizes() has no effect. turbodbc automatically picks appropriate
        return types and sizes. Method exists since PEP-249 requires it.
        """
        pass

    def setoutputsize(self, size, column=None):
        """
        setoutputsize() has no effect. turbodbc automatically picks appropriate
        input types and sizes. Method exists since PEP-249 requires it.
        """
        pass
