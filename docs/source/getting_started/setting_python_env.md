<!--
{% comment %}
Copyright 2021 IBM

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
{% endcomment %}
-->

[pyenv](https://github.com/pyenv/pyenv) is a tool that can be used to easily enable and switch between multiple versions of Python.

It can be installing with:

[MacOS]

1. Install via Homebrew

pyenv can be installed with [Homebrew](https://brew.sh) with the following command:

```bash
# Requires admin privileges
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

*Note:* If you don't have Xcode Command Line installed yet, this step will request confirmation and install it.

2. Install pyenv:

```bash
brew install pyenv 
```

3. Install Python (CodeFlare has been tested with 3.8.6):

```bash
pyenv install 3.8.6
```

4. Set global default:
```bash
pyenv global 3.8.6
```
and verify it worked:

```bash
pyenv version
3.8.6 (set by /Users/<user>/.pyenv/version)
```

5. Set up shell path:

Add the following to your `~/.bash_profile` (*Note*: you may have to create the the file)

```bash
export PYENV_ROOT="$HOME/.pyenv" 
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init --path)"

eval "$(pyenv init -)"
```

You will have to source your profile for changes to take affect:

```bash
source ~/.bash_profile
```

6. Confirm Python version

```bash
python --version
Python 3.8.6
```

