import collections.abc
import pickle
import sys
import typing
import warnings
from contextlib import contextmanager
from unittest import TestCase, main
from mypy_extensions import TypedDict, _TypedDictMeta, i64, i32, i16, u8


@contextmanager
def assert_typeddict_deprecated(testcase):
    with testcase.assertWarnsRegex(
        DeprecationWarning, "mypy_extensions.TypedDict is deprecated"
    ):
        yield


@contextmanager
def ignore_typeddict_deprecation():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=DeprecationWarning)
        yield


class BaseTestCase(TestCase):

    def assertIsSubclass(self, cls, class_or_tuple, msg=None):
        if not issubclass(cls, class_or_tuple):
            message = '%r is not a subclass of %r' % (cls, class_or_tuple)
            if msg is not None:
                message += ' : %s' % msg
            raise self.failureException(message)

    def assertNotIsSubclass(self, cls, class_or_tuple, msg=None):
        if issubclass(cls, class_or_tuple):
            message = '%r is a subclass of %r' % (cls, class_or_tuple)
            if msg is not None:
                message += ' : %s' % msg
            raise self.failureException(message)


with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=DeprecationWarning)

    Label = TypedDict('Label', [('label', str)])

    class Point2D(TypedDict):
        x: int
        y: int

    class LabelPoint2D(Point2D, Label): ...

    class Options(TypedDict, total=False):
        log_level: int
        log_path: str


class TypedDictTests(BaseTestCase):
    @contextmanager
    def assert_typeddict_deprecated(self):
        with self.assertWarnsRegex(
            DeprecationWarning, "mypy_extensions.TypedDict is deprecated"
        ):
            yield

    def test_basics_iterable_syntax(self):
        with self.assert_typeddict_deprecated():
            Emp = TypedDict('Emp', {'name': str, 'id': int})
        self.assertIsSubclass(Emp, dict)
        self.assertIsSubclass(Emp, typing.MutableMapping)
        self.assertNotIsSubclass(Emp, collections.abc.Sequence)
        jim = Emp(name='Jim', id=1)
        self.assertIs(type(jim), dict)
        self.assertEqual(jim['name'], 'Jim')
        self.assertEqual(jim['id'], 1)
        self.assertEqual(Emp.__name__, 'Emp')
        self.assertEqual(Emp.__module__, __name__)
        self.assertEqual(Emp.__bases__, (dict,))
        self.assertEqual(Emp.__annotations__, {'name': str, 'id': int})
        self.assertEqual(Emp.__total__, True)

    def test_basics_keywords_syntax(self):
        with self.assert_typeddict_deprecated():
            Emp = TypedDict('Emp', name=str, id=int)
        self.assertIsSubclass(Emp, dict)
        self.assertIsSubclass(Emp, typing.MutableMapping)
        self.assertNotIsSubclass(Emp, collections.abc.Sequence)
        jim = Emp(name='Jim', id=1)  # type: ignore # mypy doesn't support keyword syntax yet
        self.assertIs(type(jim), dict)
        self.assertEqual(jim['name'], 'Jim')
        self.assertEqual(jim['id'], 1)
        self.assertEqual(Emp.__name__, 'Emp')
        self.assertEqual(Emp.__module__, __name__)
        self.assertEqual(Emp.__bases__, (dict,))
        self.assertEqual(Emp.__annotations__, {'name': str, 'id': int})
        self.assertEqual(Emp.__total__, True)

    def test_typeddict_errors(self):
        with self.assert_typeddict_deprecated():
            Emp = TypedDict('Emp', {'name': str, 'id': int})
        self.assertEqual(TypedDict.__module__, 'mypy_extensions')
        jim = Emp(name='Jim', id=1)
        with self.assertRaises(TypeError):
            isinstance({}, Emp)  # type: ignore
        with self.assertRaises(TypeError):
            isinstance(jim, Emp)  # type: ignore
        with self.assertRaises(TypeError):
            issubclass(dict, Emp)  # type: ignore
        with self.assertRaises(TypeError), self.assert_typeddict_deprecated():
            TypedDict('Hi', x=())
        with self.assertRaises(TypeError), self.assert_typeddict_deprecated():
            TypedDict('Hi', [('x', int), ('y', ())])
        with self.assertRaises(TypeError):
            TypedDict('Hi', [('x', int)], y=int)

    def test_py36_class_syntax_usage(self):
        self.assertEqual(LabelPoint2D.__name__, 'LabelPoint2D')  # noqa
        self.assertEqual(LabelPoint2D.__module__, __name__)  # noqa
        self.assertEqual(LabelPoint2D.__annotations__, {'x': int, 'y': int, 'label': str})  # noqa
        self.assertEqual(LabelPoint2D.__bases__, (dict,))  # noqa
        self.assertEqual(LabelPoint2D.__total__, True)  # noqa
        self.assertNotIsSubclass(LabelPoint2D, typing.Sequence)  # noqa
        not_origin = Point2D(x=0, y=1)  # noqa
        self.assertEqual(not_origin['x'], 0)
        self.assertEqual(not_origin['y'], 1)
        other = LabelPoint2D(x=0, y=1, label='hi')  # noqa
        self.assertEqual(other['label'], 'hi')

    def test_py36_class_usage_emits_deprecations(self):
        with self.assert_typeddict_deprecated():
            class Foo(TypedDict):
                bar: int

    def test_pickle(self):
        global EmpD  # pickle wants to reference the class by name
        with self.assert_typeddict_deprecated():
            EmpD = TypedDict('EmpD', name=str, id=int)
        jane = EmpD({'name': 'jane', 'id': 37})
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            z = pickle.dumps(jane, proto)
            jane2 = pickle.loads(z)
            self.assertEqual(jane2, jane)
            self.assertEqual(jane2, {'name': 'jane', 'id': 37})
            ZZ = pickle.dumps(EmpD, proto)
            EmpDnew = pickle.loads(ZZ)
            self.assertEqual(EmpDnew({'name': 'jane', 'id': 37}), jane)

    def test_optional(self):
        with self.assert_typeddict_deprecated():
            EmpD = TypedDict('EmpD', name=str, id=int)

        self.assertEqual(typing.Optional[EmpD], typing.Union[None, EmpD])
        self.assertNotEqual(typing.List[EmpD], typing.Tuple[EmpD])

    def test_total(self):
        with self.assert_typeddict_deprecated():
            D = TypedDict('D', {'x': int}, total=False)
        self.assertEqual(D(), {})
        self.assertEqual(D(x=1), {'x': 1})
        self.assertEqual(D.__total__, False)

        self.assertEqual(Options(), {})  # noqa
        self.assertEqual(Options(log_level=2), {'log_level': 2})  # noqa
        self.assertEqual(Options.__total__, False)  # noqa


class TypedDictContractTests(BaseTestCase):
    """Contract tests: totality, inheritance and runtime metadata must be
    consistent between the functional and class syntaxes."""

    def test_functional_total_true_metadata(self):
        with assert_typeddict_deprecated(self):
            T = TypedDict('T', {'x': int}, total=True)
        self.assertEqual(T.__annotations__, {'x': int})
        self.assertIs(T.__total__, True)

    def test_functional_total_false_metadata(self):
        with assert_typeddict_deprecated(self):
            T = TypedDict('T', {'x': int}, total=False)
        self.assertEqual(T.__annotations__, {'x': int})
        self.assertIs(T.__total__, False)

    def test_class_total_false_metadata(self):
        with assert_typeddict_deprecated(self):
            class T(TypedDict, total=False):
                x: int
        self.assertEqual(T.__annotations__, {'x': int})
        self.assertIs(T.__total__, False)

    def test_total_not_inherited_from_base(self):
        # A subclass that does not redeclare total= gets total=True,
        # even if its base is non-total.
        with ignore_typeddict_deprecation():
            class Base(TypedDict, total=False):
                x: int
            class Child(Base):
                y: int
        self.assertIs(Base.__total__, False)
        self.assertIs(Child.__total__, True)
        self.assertEqual(Child.__annotations__, {'x': int, 'y': int})

    def test_explicit_total_overrides_total_base(self):
        with ignore_typeddict_deprecation():
            class Base(TypedDict):
                x: int
            class Child(Base, total=False):
                y: int
        self.assertIs(Base.__total__, True)
        self.assertIs(Child.__total__, False)

    def test_multilevel_inheritance_order_and_types(self):
        with ignore_typeddict_deprecation():
            class A(TypedDict):
                a: int
            B = TypedDict('B', {'b': str})
            class C(A, B):
                c: float
            class D(C):
                d: bytes
        self.assertEqual(list(C.__annotations__), ['a', 'b', 'c'])
        self.assertEqual(C.__annotations__, {'a': int, 'b': str, 'c': float})
        self.assertEqual(
            D.__annotations__, {'a': int, 'b': str, 'c': float, 'd': bytes})
        self.assertIs(D.__total__, True)

    def test_duplicate_field_child_wins_position_stable(self):
        # Redeclaring a base field is allowed: the child's type wins and
        # the field keeps its original (base) position.
        with ignore_typeddict_deprecation():
            class Base(TypedDict):
                x: int
                y: str
            class Child(Base):
                x: str
        self.assertEqual(Child.__annotations__, {'x': str, 'y': str})
        self.assertEqual(list(Child.__annotations__), ['x', 'y'])
        self.assertEqual(Base.__annotations__, {'x': int, 'y': str})

    def test_functional_and_class_syntax_equivalent(self):
        with ignore_typeddict_deprecation():
            Func = TypedDict('Func', {'x': int, 'y': str}, total=False)
            class Klass(TypedDict, total=False):
                x: int
                y: str
        self.assertEqual(Func.__annotations__, Klass.__annotations__)
        self.assertEqual(Func.__total__, Klass.__total__)
        self.assertEqual(type(Func), type(Klass))
        self.assertEqual(Func(x=1, y='a'), Klass(x=1, y='a'))

    def test_empty_fields(self):
        with ignore_typeddict_deprecation():
            EmptyFunc = TypedDict('EmptyFunc', {})
            class EmptyClass(TypedDict):
                pass
            class EmptyChild(EmptyClass, total=False):
                pass
        self.assertEqual(EmptyFunc.__annotations__, {})
        self.assertEqual(EmptyClass.__annotations__, {})
        self.assertEqual(EmptyChild.__annotations__, {})
        self.assertIs(EmptyFunc.__total__, True)
        self.assertIs(EmptyChild.__total__, False)
        self.assertEqual(EmptyFunc(), {})

    def test_field_names_conflicting_with_dict_attrs(self):
        with ignore_typeddict_deprecation():
            T = TypedDict('T', {'keys': int, 'total': str, 'items': float})
        self.assertEqual(
            T.__annotations__, {'keys': int, 'total': str, 'items': float})
        self.assertIs(T.__total__, True)
        inst = T(keys=1, total='a', items=2.0)
        self.assertEqual(inst, {'keys': 1, 'total': 'a', 'items': 2.0})
        self.assertEqual(inst['keys'], 1)

    def test_annotations_isolation_between_base_and_child(self):
        with ignore_typeddict_deprecation():
            class Base(TypedDict):
                x: int
            class Child(Base):
                y: int
        self.assertIsNot(Base.__annotations__, Child.__annotations__)
        Child.__annotations__['z'] = bytes
        self.assertEqual(Base.__annotations__, {'x': int})
        self.assertEqual(set(Child.__annotations__), {'x', 'y', 'z'})

    def test_instance_is_plain_mutable_dict_without_validation(self):
        with ignore_typeddict_deprecation():
            class Movie(TypedDict):
                name: str
                year: int
        movie = Movie(name='Blade Runner', year=1982)
        self.assertIs(type(movie), dict)
        self.assertIsInstance(movie, dict)
        # No runtime validation of values or keys.
        movie['year'] = 'not an int'
        movie['extra'] = object()
        del movie['name']
        self.assertNotIn('name', movie)
        # Missing/extra keys are accepted at runtime.
        self.assertEqual(Movie(), {})
        self.assertEqual(Movie(year='x'), {'year': 'x'})

    def test_deprecation_warning_functional_and_class(self):
        with assert_typeddict_deprecated(self):
            TypedDict('W', {'x': int})
        with assert_typeddict_deprecated(self):
            TypedDict('W2', x=int, total=False)
        with assert_typeddict_deprecated(self):
            class W3(TypedDict, total=False):
                x: int

    def test_legacy_namespace_annotations_path(self):
        # Pre-3.14 class syntax put __annotations__ directly in the class
        # namespace; the metaclass must still honor that path.
        with ignore_typeddict_deprecation():
            class Base(TypedDict):
                x: int
        with assert_typeddict_deprecated(self):
            Legacy = _TypedDictMeta(
                'Legacy', (Base,),
                {'__annotations__': {'y': str}, '__total__': False})
        self.assertEqual(Legacy.__annotations__, {'x': int, 'y': str})
        self.assertIs(Legacy.__total__, False)
        self.assertEqual(Legacy(x=1, y='a'), {'x': 1, 'y': 'a'})

    def test_invalid_types_and_arguments_still_raise(self):
        with self.assertRaises(TypeError), assert_typeddict_deprecated(self):
            TypedDict('Hi', {'x': ()})
        with self.assertRaises(TypeError), assert_typeddict_deprecated(self):
            TypedDict('Hi', [('x', int), ('y', ())])
        with self.assertRaises(TypeError):
            TypedDict('Hi', [('x', int)], y=int)
        with ignore_typeddict_deprecation():
            with self.assertRaises(TypeError):
                class Bad(TypedDict):
                    x: ()


native_int_types = [i64, i32, i16, u8]


class MypycNativeIntTests(TestCase):
    def test_construction(self):
        for native_int in native_int_types:
            self.assert_same(native_int(), 0)

            self.assert_same(native_int(0), 0)
            self.assert_same(native_int(1), 1)
            self.assert_same(native_int(-3), -3)
            self.assert_same(native_int(2**64), 2**64)
            self.assert_same(native_int(-2**64), -2**64)

            self.assert_same(native_int(1.234), 1)
            self.assert_same(native_int(2.634), 2)
            self.assert_same(native_int(-1.234), -1)
            self.assert_same(native_int(-2.634), -2)

            self.assert_same(native_int("0"), 0)
            self.assert_same(native_int("123"), 123)
            self.assert_same(native_int("abc", 16), 2748)
            self.assert_same(native_int("-101", base=2), -5)

    def test_isinstance(self):
        for native_int in native_int_types:
            assert isinstance(0, native_int)
            assert isinstance(1234, native_int)
            assert isinstance(True, native_int)
            assert not isinstance(1.0, native_int)

    def test_docstring(self):
        for native_int in native_int_types:
            # Just check that a docstring exists
            assert native_int.__doc__

    def assert_same(self, x, y):
        assert type(x) is type(y)
        assert x == y


class DeprecationTests(TestCase):
    def test_no_return_deprecation(self):
        del sys.modules["mypy_extensions"]
        with self.assertWarnsRegex(
            DeprecationWarning, "'mypy_extensions.NoReturn' is deprecated"
        ):
            import mypy_extensions
            mypy_extensions.NoReturn

        del sys.modules["mypy_extensions"]
        with self.assertWarnsRegex(
            DeprecationWarning, "'mypy_extensions.NoReturn' is deprecated"
        ):
            from mypy_extensions import NoReturn  # noqa: F401


if __name__ == '__main__':
    main()
