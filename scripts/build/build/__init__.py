import logging
import os
import shutil
from pathlib import Path
from enum import Enum, auto
from typing import Sequence

from .targets import BUILD_TARGETS
from builders.builder import BuilderOptions

from pw_build.build_recipe import BuildRecipe, BuildCommand
from pw_build.project_builder import ProjectBuilder, run_builds
from pw_watch.watch import run_watch, watch_setup


class BuildSteps(Enum):
    GENERATED = auto()


class Context:
    """Represents a grouped list of platform/board/app builders to use

         to generate make/ninja instructions and to compile.
      """

    def __init__(self, runner, repository_path: str, output_prefix: str):
        self.builders = []
        self.runner = runner
        self.repository_path = repository_path
        self.output_prefix = output_prefix
        self.completed_steps = set()

    def SetupBuilders(self, targets: Sequence[str], options: BuilderOptions):
        """
        Configures internal builders for the given platform/board/app
        combination.
        """

        self.builders = []
        for target in targets:
            found = False
            for choice in BUILD_TARGETS:
                builder = choice.Create(target, self.runner, self.repository_path,
                                        self.output_prefix, options)
                if builder:
                    self.builders.append(builder)
                    found = True

            if not found:
                logging.error(f"Target '{target}' could not be found. Nothing executed for it")

        # whenever builders change, assume generation is required again
        self.completed_steps.discard(BuildSteps.GENERATED)

    def Generate(self):
        """
        Performs a build generation IF code generation has not yet been
        performed.
        """
        if BuildSteps.GENERATED in self.completed_steps:
            return

        self.runner.StartCommandExecution()

        for builder in self.builders:
            logging.info('Generating %s', builder.output_dir)
            builder.generate()

        self.completed_steps.add(BuildSteps.GENERATED)

    def Build(self):
        self.Generate()

        for builder in self.builders:
            logging.info('Building %s', builder.output_dir)
            builder.build()

    def build_recipes(self) -> list[BuildRecipe]:
        recipes: list[BuildRecipe] = []
        for name, steps in self.runner.recipe_steps.items():
            recipes.append(
                BuildRecipe(
                    build_dir=Path(self.output_prefix) / name,
                    title=name,
                    steps=[BuildCommand(command=cmd) for cmd in steps]))

        return recipes

    def run_pw_build(self) -> None:
        root_logfile = Path(self.output_prefix) / 'build.txt'
        root_logger = logging.getLogger('pw_build')

        project_builder = ProjectBuilder(
            build_recipes=self.build_recipes(),
            banners=True,
            log_level=logging.INFO,
            separate_build_file_logging=True,
            root_logger=root_logger,
            root_logfile=root_logfile,
        )
        # project_builder.use_stdout_proxy()
        # run_builds(project_builder, workers=2)

        event_handler, exclude_list = watch_setup(
            project_builder,
            parallel=True,
            parallel_workers=3,
            fullscreen=True,
            logfile=root_logfile,
            separate_logfiles=True,
        )

        run_watch(
            event_handler,
            exclude_list,
            fullscreen=True,
        )

    def CleanOutputDirectories(self):
        for builder in self.builders:
            logging.warn('Cleaning %s', builder.output_dir)
            if os.path.exists(builder.output_dir):
                shutil.rmtree(builder.output_dir)

        # any generated output was cleaned
        self.completed_steps.discard(BuildSteps.GENERATED)

    def CreateArtifactArchives(self, directory: str):
        logging.info('Copying build artifacts to %s', directory)
        if not os.path.exists(directory):
            os.makedirs(directory)
        for builder in self.builders:
            # FIXME: builder subdir...
            builder.CompressArtifacts(os.path.join(
                directory, f'{builder.identifier}.tar.gz'))

    def CopyArtifactsTo(self, path: str):
        logging.info('Copying build artifacts to %s', path)
        if not os.path.exists(path):
            os.makedirs(path)

        for builder in self.builders:
            # FIXME: builder subdir...
            builder.CopyArtifacts(os.path.join(path, builder.identifier))
