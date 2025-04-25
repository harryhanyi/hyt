import mhy.protostar.core.parameter as pa
import mhy.python.core.compatible as compat
from mhy.maya.rig.base_actions import BaseRigUtilAction
import mhy.maya.rig.workarea as wa
import mhy.maya.rig.utils as util
compat.reload(wa)

class AssetConfig(BaseRigUtilAction):
    """Asset path configuration action.

    From user-provided workarea root path, project name, and character name,
    Configure the following source directories and file paths:

        + marker data file
        + ctrl data file
        + skeleton path
        + rig mesh path
        + connection data path
        + set data export path
        + deformer data path
        + deformer data path
        + weights deformer data path
        + pose data path
        + picker file path
        + metahuman rig file path
    """

    # --- input parameters

    @pa.dir_param()
    def workarea_path(self):
        """The workarea root path"""

    @pa.str_param()
    def project_name(self):
        """The project name."""

    @pa.str_param()
    def char_name(self):
        """The character name."""

    @pa.enum_param(items=('body', 'face'))
    def rig_type(self):
        """The rig type."""
        

    # --- output parameters

    @pa.file_param(output=True, ext='json')
    def marker_file(self):
        """The resolved marker file path."""

    @pa.file_param(output=True, ext='json')
    def ctrl_file(self):
        """The resolved ctrl shape data file path."""
        
    @pa.dir_param(output=True)
    def skel_path(self):
        """The resolved skeleton directory path.
        All source skeleton files goes here.
        """

    @pa.dir_param(output=True)
    def rigmesh_path(self):
        """The resolved mesh directory path.
        All source mesh files goes here.
        """

    @pa.dir_param(output=True)
    def mesh_path(self):
        """The resolved mesh directory path.
        Where all published mesh files are.
        """
        
    @pa.dir_param(output=True)
    def target_path(self):
        """The resolved sculpted target meshes directory path.
        """

    @pa.dir_param(output=True)
    def connection_path(self):
        """The resolved connection data directory path.
        All connection data files goes here.
        """

    @pa.file_param(output=True, ext='json')
    def connection_file(self):
        """The resolved connections data file path."""
        
    @pa.file_param(output=True, ext='json')
    def pr_connection_file(self):
        """The resolved pose rig connections data file path."""

    @pa.file_param(output=True, ext='json')
    def export_set_file(self):
        """The resolved export set data file path."""

    @pa.dir_param(output=True)
    def deformer_path(self):
        """The resolved deformer data directory path.
        All deformer data files goes here.
        """
        
    @pa.dir_param(output=True)
    def blend_shape_path(self):
        """The resolved blend shape data directory path.
        All blend shape data files goes here.
        """
        
    @pa.dir_param(output=True)
    def skin_cluster_path(self):
        """The resolved skin cluster data directory path.
        All skin cluster data files goes here.
        """

    @pa.dir_param(output=True)
    def wts_deformer_path(self):
        """The resolved weights deformer data directory path.
        All weights deformer data files goes here.
        """

    @pa.dir_param(output=True)
    def pose_path(self):
        """The resolved pose data directory path.
        All pose data files goes here.
        """

    @pa.dir_param(output=True)
    def picker_path(self):
        """The resolved picker data directory path.
        All picker data files goes here.
        """
        
    @pa.dir_param(output=True)
    def metahuman_path(self):
        """The resolved metahuman rig and maps directory path.
        All metahuman files goes here.
        """
        
    @pa.dir_param(output=True)
    def shader_path(self):
        """The resolved shader data directory path.
        All shader data goes here.
        """
        
    @pa.file_param(output=True, ext='json')
    def attr_file(self):
        """The resolved attribute setting data directory path.
        All attribute setting data goes here.
        """

    @pa.file_param(output=True, ext='json')
    def texture_driver_data_path(self):
        """The resolved picker data directory path.
        All pose data files goes here.
        """

    @pa.file_param(output=True, ext='ma')
    def rig_file(self):
        """The output rig file."""

    # --- end of parameter definition

    def run(self):
        """Executes this action."""
        self.configure_paths()
        self.create_workarea()
        util.init_rig_root_groups()

        # create rig root structure and embed rig data
        rig_root = util.get_or_create_rig_root()
        for attr, val in zip(
            ('project_name', 'char_name', 'rig_type'),
            (self.project_name.value,
             self.char_name.value,
             self.rig_type.enum_value)
        ):
            attr = rig_root.add_attr('string', name=attr)
            attr.value = val
            attr.locked = True

    def __get_path_args(self):
        workarea_path = self.workarea_path.value
        proj = self.project_name.value
        char = self.char_name.value
        rig_type = self.rig_type.enum_value

        args = (workarea_path, proj, char)
        kwargs = {'rig_type': rig_type}

        return args, kwargs

    def configure_paths(self):
        """Configures resource paths and set output parameters."""
        args, kwargs = self.__get_path_args()

        self.marker_file.value = wa.marker_data_file(*args, **kwargs)
        self.ctrl_file.value = wa.ctrl_data_file(*args, **kwargs)
        self.connection_file.value = wa.connection_data_file(*args, **kwargs)
        self.pr_connection_file.value = wa.pr_connection_data_file(*args, **kwargs)
        self.export_set_file.value = wa.set_data_file(*args, **kwargs)
        self.skel_path.value = wa.skeleton_path(*args, **kwargs)
        self.rigmesh_path.value = wa.rigmesh_path(*args, **kwargs)
        self.target_path.value = wa.target_path(*args, **kwargs)
        self.connection_path.value = wa.connection_path(
            *args, **kwargs)
        self.deformer_path.value = wa.deformer_path(*args, **kwargs)
        self.blend_shape_path.value = wa.blend_shape_path(*args, **kwargs)
        self.skin_cluster_path.value = wa.skin_cluster_path(*args, **kwargs)
        self.wts_deformer_path.value = wa.wts_deformer_path(
            *args, **kwargs)
        self.pose_path.value = wa.pose_path(*args, **kwargs)
        self.picker_path.value = wa.picker_path(*args, **kwargs)
        self.metahuman_path.value = wa.metahuman_path(*args, **kwargs)
        self.shader_path.value = wa.shader_path(*args, **kwargs)
        self.attr_file.value = wa.attribute_data_file(*args, **kwargs)
        self.texture_driver_data_path.value = wa.texture_driver_path(*args, **kwargs)
        self.rig_file.value = wa.rig_file(*args, **kwargs)

    def create_workarea(self):
        """Creates and sets maya project folders for the current character
        as the workarea folders.
        """
        args, kwargs = self.__get_path_args()
        wa.create_workarea(*args, **kwargs)
