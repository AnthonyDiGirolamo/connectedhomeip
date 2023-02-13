# Copyright (c) 2021 Project CHIP Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import shlex
from typing import Optional

class PrintOnlyRunner:
    def __init__(self, output_file, root: str):
        self.output_file = output_file
        self.dry_run = True
        self.root = root
        self.recipe_steps = {}

    def StartCommandExecution(self):
        pass
        # self.output_file.write(
        #     "# Commands will be run in CHIP project root.\n")
        # self.output_file.write('cd "%s"\n\n' % self.root)

    def Run(self, cmd: list[str], title: Optional[str] = None,
            identifier: Optional[str] = None) -> None:

        steps = self.recipe_steps.get(identifier, [])
        steps.append(cmd)
        self.recipe_steps[identifier] = steps

        # if title:
        #     self.output_file.write("# " + title + "\n")

        # self.output_file.write(
        #     " ".join([shlex.quote(part) for part in cmd]) + "\n")

        # self.output_file.write("\n")
