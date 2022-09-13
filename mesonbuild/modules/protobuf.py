import os
import typing as T

from . import ExtensionModule, ModuleInfo, ModuleReturnValue
from ..build import InvalidArguments, CustomTarget
from ..interpreterbase import noPosargs, typed_kwargs, KwargInfo, ContainerTypeInfo
from ..mesonlib import File

if T.TYPE_CHECKING:
    from . import ModuleState
    from ..interpreter import Interpreter
    from ..interpreter.interpreter import SourceInputs

    class BindgenArgs(T.TypedDict):
        protos: T.List[SourceInputs]
        lang: str
        # proto_path: str
        install_staging: bool


class ProtobufModule(ExtensionModule):

    INFO = ModuleInfo('protobuf', '0.1', unstable=True)

    def __init__(self, interpreter: 'Interpreter'):
        super().__init__(interpreter)
        self.supported_langs = {
            'cpp': ['@BASENAME@.pb.h', '@BASENAME@.pb.cc'],
            'python': ['@BASENAME@_pb2.py'],
        }
        self.methods.update({
            'bindgen': self.bindgen,
        })

    @noPosargs
    @typed_kwargs(
        'protobuf.bindgen',
        KwargInfo('protos', ContainerTypeInfo(list, (File, str), allow_empty=False)),
        KwargInfo('lang', str, required=True),
        # KwargInfo('proto_path', str, default='@CURRENT_SOURCE_DIR@'),
        KwargInfo('install_staging', bool, default=False),
    )
    def bindgen(self, state: 'ModuleState', args: T.List, kwargs: 'BindgenArgs') -> ModuleReturnValue:
        lang = kwargs['lang']
        if lang not in self.supported_langs:
            raise InvalidArguments(f'unknown or unsupported language \'{lang}\'')

        protoc_bin = state.find_program('protoc')
        sources = self.interpreter.source_strings_to_files(kwargs['protos'])
        targets = []
        for file in sources:
            subdir = os.path.join(os.path.dirname(file.fname), '')
            generated_files = [subdir + x for x in self.supported_langs[lang]]
            t = CustomTarget(
                f'pb-bindgen-{lang}-{file.fname}'.replace('/', '_'),
                state.subdir, state.subproject, state.environment,
                protoc_bin.get_command() + [
                    f'--proto_path=@CURRENT_SOURCE_DIR@',
                    f'--{lang}_out={state.environment.get_build_dir()}',
                    '@INPUT@'
                ],
                [file],
                generated_files,
                build_by_default=True,
                install=kwargs['install_staging'],
            )
            targets.append(t)

        return ModuleReturnValue(targets, targets)


def initialize(interpreter: 'Interpreter') -> ProtobufModule:
    return ProtobufModule(interpreter)
