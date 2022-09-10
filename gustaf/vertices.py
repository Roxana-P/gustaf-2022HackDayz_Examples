"""gustaf/gustaf/vertices.py

Vertices. Base of all "Mesh" geometries.
"""

import copy

import numpy as np

from gustaf import settings
from gustaf import utils
from gustaf import show
from gustaf import helpers
from gustaf._base import GustafBase


class Vertices(GustafBase):

    kind = "vertex"

    __slots__ = [
        "_vertices",
        "_computed"
        "vis_dict",
        "vertexdata",
    ]

    def __init__(
            self,
            vertices=None,
    ):
        """
        Vertices. It has vertices.

        Parameters
        -----------
        vertices: (n, d) np.ndarray

        Returns
        --------
        None

        Attributes
        -----------
        whatami: str
        vertices: np.ndarray
        
        """
        if vertices is not None:
            self.vertices = vertices

        self._computed = helpers.data.ComputedMeshData(self)

        self.vis_dict = dict()
        self.vertexdata = dict()

    @property
    def vertices(self):
        """
        Returns vertices

        Parameters
        -----------
        None

        Returns
        --------
        vertices: (n, d) np.ndarray
        """
        self._logd("returning vertices")
        return self._vertices


    @vertices.setter:
    def vertices(self, vs):
        """
        Vertices setter. This will saved as a tracked array.

        Parameters
        -----------
        vs: (n, d) np.ndarray

        Returns
        --------
        None
        """
        self._logd("setting vertices")
        self._vertices = helpers.data.make_tracked_array(
            vs,
            settings.FLOAT_DTYPE
        )

    @property
    def whatami(self,):
        """
        Answers deep philosophical question: "what am i"?

        Parameters
        ----------
        None

        Returns
        --------
        whatami: str
          vertices
        """
        return "vertices"

    @property
    def elements(self):
        """
        Returns current connectivity. A short cut in FEM friendly term.
        Elements mean different things for different classes:
          Vertices -> vertices
          Edges -> edges
          Faces -> faces
          Volumes -> volumes

        Parameters
        -----------
        None

        Returns
        --------
        elements: (n, d) np.ndarray
          int. iff elements=None
        """
        if self.kind.startswith("vertex"):
            self._logd(
                "returning vertex ids as Vertices.elements()."
            )
            # this is just to keep the output of consistent
            return helpers.data.make_tracked_array(
                np.arange(
                    (self.vertices.shape[0], 1),
                    dtype=settings.INT_DTYPE,
                )
            )

        else:
            # naming rule in gustaf
            # all of those should be tracked array.
            elem_name = type(self).__qualname__.lower()
            self._logd(f"returning {elem_name}")
 
           return getattr(self, elem_name)

    @elements.setter
    def elements(self, elems):
        """
        Calls corresponding connectivity setter.
        A short cut in FEM friendly term.
          Vertices -> vertices
          Edges -> edges
          Faces -> faces
          Volumes -> volumes

        Parameters
        -----------
        elems: (n, d) np.ndarray

        Returns
        --------
        None
        """
        if self.kind.startswith("vertex"):
            self._logw(
                "no elements setter for vertices. doing nothing."
            )
            return None

        else:
            # naming rule in gustaf
            elem_name = type(self).__qualname__.lower()
            self._logd(f"seting {elem_name}'s connectivity.")
 
           return setattr(self, elem_name, elems)


    @helpers.data.ComputedMeshData("vertices")
    def unique_vertices(
            self,
            tolerance=None,
            **kwargs
    ):
        """
        Returns a namedtuple that holds unique vertices info.
        Unique here means "close-enough-within-tolerance".

        Parameters
        -----------
        tolerance: float
          (Optional) Default is settings.TOLERANCE
        recompute: bool
          Only applicable as keyword argument. Force re-computes.

        Returns
        --------
        unique_vertices_info: Unique2DFloats
          namedtuple with `values`, `ids`, `inverse`, `union`.
        """
        self._logd("computing unique vertices")
        if tolerance is None:
            tolerance = settings.TOLERANCE

        values, ids, inverse, union = utils.arr.close_rows(
            tolerance=tolerance
        )

        return helpers.data.Unique2DFloats(
            values,
            unique_ids,
            inverse,
            union,
        )

    @helpers.data.ComputedMeshData("vertices")
    def bounds(self):
        """
        Returns bounds of the vertices.
        Bounds means AABB of the geometry.

        Parameters
        -----------
        None

        Returns
        --------
        bounds: (d,) np.ndarray
        """
        self._logd("computing bounds")
        return utils.arr.bounds(self.vertices)


    @helpers.data.ComputedMeshData("vertices")
    def bounds_diagonal(self):
        """
        Returns diagonal vector of the bounding box.

        Parameters
        -----------
        None

        Returns
        --------
        bounds_digonal: (d,) np.ndarray
          same as `bounds[1] - bounds[0]`
        """
        self._logd("computing bounds_diagonal")
        bounds = self.bounds()
        return bounds[1] - bounds[0]
    
    @helpers.data.ComputedMeshData("vertices")
    def bounds_diagonal_norm(self):
        """
        Returns norm of bounds diagonal.

        Parameters
        -----------
        None

        Returns
        --------
        bounds_diagonal_norm: float
        """
        self._logd("computing bounds_diagonal_norm")
        return float(sum(self.bounds_diagonal() ** 2) ** .5)

    @helpers.data.ComputedMeshData(["vertices", "elements"])
    def centers(self):
        """
        Center of elements.

        Parameters
        -----------
        None

        Returns
        --------
        centers: (n_elements, d) np.ndarray
        """
        self._logd("computing centers")
        elements = self.elements()
        self.centers = self.vertices[elements].mean(axis=1)

        return self.centers

    def update_vertices(self, mask, inverse=None):
        """
        Update vertices with a mask.
        In other words, keeps only masked vertices.
        Adapted from `github.com/mikedh/trimesh`.
        Updates connectivity accordingly too.

        Parameters
        -----------
        mask: (n,) bool or int
        inverse: (len(self.vertices),) int

        Returns
        --------
        updated_self: type(self)
        """
        vertices = self.vertices.copy()

        # make mask numpy array
        mask = np.asarray(mask)

        if (
            (mask.dtype.name == "bool" and mask.all())
            or len(mask) == 0
        ):
            return self

        # create inverse mask if not passed
        if inverse is None:
            inverse = np.full(len(vertices), -1, dtype=settings.INT_DTYPE)
            if mask.dtype.kind == "b":
                inverse[mask] = np.arange(mask.sum())
            elif mask.dtype.kind == "i":
                inverse[mask] = np.arange(len(mask))
            else:
                inverse = None

        # re-index elements from inverse
        # TODO: Here could be a good place to preserve BCs.
        elements = None
        if inverse is not None and self.kind != "vertex":
            elements = self.elements.copy()
            elements = inverse[elements.reshape(-1)].reshape(
                (-1, elements.shape[1])
            )
            # remove all the elements that's not part of inverse
            elements = elements[np.unique(np.where(elements < 0)[0])]

        # apply mask
        vertices = vertices[mask]

        def update_vertexdata(obj, m, vertex_data=None):
            """
            apply mask to vertex data if there's any.
            """
            newdata = dict()
            if vertex_data is None:
                vertex_data = obj.vertexdata

            for key, values in vertex_data.items():
                newdata[key] = values[m]

            obj.vertexdata = newdata

            return obj

        # update
        self.vertices = vertices
        if elements is not None:
            self.elements = elements

        update_vertexdata(self, mask)

        return self

    def select_vertices(self, ranges):
        """
        Returns vertices inside the given range.

        Parameters
        -----------
        ranges: (d, 2) array-like
          Takes None.

        Returns
        --------
        ids: (n,) np.ndarray
        """
        return utils.arr.select_with_ranges(self.vertices, ranges)

    def remove_vertices(self, ids):
        """
        Removes vertices with given vertex ids.

        Parameters
        -----------
        ids: (n,) np.ndarray

        Returns
        --------
        new_self: type(self)
        """
        mask = np.ones(len(self.vertices), dtype=bool)
        mask[ids] = False

        return self.update_vertices(mask,)

    def referenced_vertices(self,):
        """
        Returns mask of referenced vertices.

        Parameters
        -----------
        None

        Returns
        --------
        referenced: (n,) np.ndarray
        """
        referenced = np.zeros(len(self.vertices), dtype=bool)
        referenced[self.elements] = True

        return referenced

    def remove_unreferenced_vertices(self):
        """
        Remove unreferenced vertices.
        Adapted from `github.com/mikedh/trimesh`

        Parameters
        -----------
        None

        Returns
        --------
        new_self: type(self)
        """
        if self.kind == "vertex":
            return self

        referenced = self.referenced_vertices()

        inverse = np.zeros(len(self.vertices), dtype=settings.INT_DTYPE)
        inverse[referenced] = np.arange(referenced.sum())

        return self.update_vertices(
            mask=referenced,
            inverse=inverse,
        )

    def merge_vertices(
            self,
            tolerance=None
    ):
        """
        Based on unique vertices, merge vertices if it is mergeable.

        Parameters
        -----------
        tolerance: float
          Default is settings.TOLERANCE

        Returns
        --------
        merged_self: type(self)
        """
        unique_vs = self.unique_vertices()

        self._logd("number of vertices")
        self._logd(f"  before merge: {len(self.vertices)}")
        self._logd(f"  after merge: {len(unique_vs.ids)}")

        return self.update_vertices(
            mask=unique_vs.ids,
            inverse=unique_vs.inverse,
        )

    def showable(self, **kwargs):
        """
        Returns showable object, meaning object of visualization backend.

        Parameters
        -----------
        **kwargs:

        Returns
        --------
        showable: obj
          Obj of `gustaf.settings.VISUALIZATION_BACKEND`
        """
        return show.make_showable(self, **kwargs)

    def show(self, **kwargs):
        """
        Show current object using visualization backend.

        Parameters
        -----------
        **kwargs:


        Returns
        --------
        None
        """
        return show.show(self, **kwargs)

    def copy(self):
        """
        Returns deepcopy of self.

        Parameters
        -----------
        None

        Returns
        --------
        selfcopy: type(self)
        """
        # all attributes are deepcopy-able
        return copy.deepcopy(self)

    @classmethod
    def concat(cls, *instances):
        """
        Sequentially put them together to make one object.

        Parameters
        -----------
        *instances: *type(cls)
          Allows one iterable object also.

        Returns
        --------
        one_instance: type(cls)
        """
        def is_concatable(inst):
            """
            Return true, if it is same as type(cls)
            """
            if cls.__name__.startswith(inst.__class__.__name__):
                return True
            else:
                return False

        # If only one instance is given and it is iterable, adjust
        # so that we will just iterate that.
        if (
            len(instances) == 1
            and not isinstance(instances[0], str)
            and hasattr(instances[0], "__iter__")
        ):
            instances = instances[0]

        vertices = []
        haselem = cls.kind != "vertex"
        if haselem:
            elements = []

        # check if everything is "concatable".
        for ins in instances:
            if not is_concatable(ins):
                raise TypeError(
                    "Can't concat. One of the instances is not "
                    f"`{cls.__name__}`."
                )

            # make sure each element index starts from 0 & end at len(vertices)
            tmp_ins = ins.copy().remove_unreferenced_vertices()

            vertices.append(
                tmp_ins.vertices.copy()
            )

            if haselem:
                if len(elements) == 0:
                    elements.append(
                        tmp_ins.elements().copy()
                    )
                    e_offset = elements[-1].max() + 1

                else:
                    elements.append(
                        tmp_ins.elements().copy() + e_offset
                    )
                    e_offset = elements[-1].max() + 1

        if haselem:
            return cls(
                vertices=np.vstack(vertices),
                elements=np.vstack(elements),
            )

        else:
            return Vertices(
                vertices=np.vstack(vertices),
            )

    def __add__(self, to_add):
        """
        Concat in form of +.

        Parameters
        -----------
        to_add: type(self)

        Returns
        --------
        added: type(self)
        """
        return type(self).concat(self, to_add)
