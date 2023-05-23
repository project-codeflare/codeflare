<!--
{% comment %}
Copyright 2021, 2022, 2023 IBM

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

<p align="center">
<img src="./images/codeflare_square.svg" width="200" height="200">
</p>

<!--
<p align="center">
<img src="./images/pipelines.svg" width="340" height="207">
</p> 
-->

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](http://www.apache.org/licenses/LICENSE-2.0)
[![Build
Status](https://travis-ci.com/project-codeflare/codeflare.svg?branch=main)](https://travis-ci.com/project-codeflare/codeflare.svg?branch=main) 

[![GitHub](https://img.shields.io/badge/issue_tracking-github-blue.svg)](https://github.com/project-codeflare/codeflare/issues)
[![GitHub](https://img.shields.io/badge/CodeFlare-Join%20Slack-blue)](s)

<!-- >> **⚠ UPDATE**  
> CodeFlare is evolving! Check our [updates](https://github.com/project-codeflare/codeflare#pipeline-execution-and-scaling) for CodeFlare Pipelines and related contributions to Ray Workflows under Ray project. -->

# Simplified and efficient scaling of AI/ML on the Hybrid Cloud

CodeFlare provides a simple, user-friendly abstraction for developing, scaling, and managing resources for distributed AI/ML on the Hybrid Cloud platform with OpenShift Container Platform.

It consists of the following main components:

* **Simplified user experience**:
CodeFlare [SDK](codeflare-sdk) and [CLI](codeflare-cli) to define, develop, and control remote distributed compute jobs and infrastructure from either a python-based environment or command-line interface

* **Efficient resource management**:
Multi-Cluster Application Dispatcher [(MCAD)](mcad) for queueing, resource quotas, and management of batch jobs. And, Instascale, for on-demand resource scaling of an OpenShift cluster

* **Automated and streamlined deployment**:
[CodeFlare Operator](codeflare-operator) for automating deployment and configuration of the Project CodeFlare stack

With CodeFlare stack, users automate and simplify scale-out of steps like data pre-processing, distributed model training, adaptation and validation. 

Through transparent integration with [Ray](https://github.com/ray-project/ray) and [PyTorch](https://github.com/pytorch/pytorch) framewokrs, and the rich library ecosystem that run on them, CodeFlare enables data scientists to **spend more time on model developement and minimum time on resource deployment and scaling**. 

See the CodeFlare stack below and how to get started.

<p align="center">
<img src="./images/codeflare_stack.svg" width="1012" height="1040">
</p>

---

## Project CodeFlare Ecosystem

In addition to running standalone, Project CodeFlare is deployed as part of and integrated with the [Open Data Hub][distributed-workloads], leveraging [OpenShift Container Platform](https://www.openshift.com). 

With OpenShift can be deployed anywhere, from on-prem to cloud, and integrate easily with other cloud-native ecosystems.

## Getting Started

### Learning

Watch [this video][youtube-demo] for an introduction to Project CodeFlare and what the
stack can do.

### Quick Start

To get started using the Project CodeFlare stack, try this [end-to-end example][quickstart]!

For more basic walk-throughs and in-depth tutorials, see our [demo notebooks][demos]!

## Development

See more details in any of the component repos linked above, or get started by taking a look at the [project board][board] for open tasks/issues!

### Architecture

We attempt to document all architectural decisions in our [ADR documents][adr]. Start here to understand the architectural details of Project CodeFlare.

---

## Getting Involved

Join our [Slack community][slack] to get involved or ask questions.

## Blog

CodeFlare related blogs are published on our [Medium publication](https://medium.com/codeflare).

## License

CodeFlare is an open-source project with an [Apache 2.0 license](LICENSE).

[codeflare-sdk]: https://github.com/project-codeflare/codeflare-sdk
[codeflare-cli]: https://github.com/project-codeflare/codeflare-cli
[mcad]: https://github.com/project-codeflare/multi-cluster-app-dispatcher
[instascale]: https://github.com/project-codeflare/instascale
[codeflare-operator]: https://github.com/project-codeflare/codeflare-operator
[distributed-workloads]: https://github.com/opendatahub-io/distributed-workloads
[quickstart]: https://github.com/opendatahub-io/distributed-workloads/blob/main/Quick-Start.md
[slack]: https://invite.playplay.io/invite?team_id=T04KQQBTDN3
[adr]: https://github.com/project-codeflare/adr
[demos]: https://github.com/project-codeflare/codeflare-sdk/tree/main/demo-notebooks/guided-demos
[board]: https://github.com/orgs/project-codeflare/projects/8
[youtube-demo]: https://www.youtube.com/watch?v=OAzFBFL5B0k