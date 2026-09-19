This issue lists Renovate updates and detected dependencies. Read the [Dependency Dashboard](https://docs.renovatebot.com/key-concepts/dashboard/) docs to learn more.<br>[View this repository on the Mend.io Web Portal](https://developer.mend.io/github/nolte/kamerplanter).

## Deprecations / Replacements
> [!WARNING]
The following dependencies are either deprecated or have replacements available.

| Datasource | Package | Replacement PR? |
|------------|------|--------------|
| npm | `@types/react-grid-layout` | ![Unavailable](https://img.shields.io/badge/unavailable-orange?style=flat-square) |

## Open

The following updates have all been created. To force a retry/rebase of any, click on a checkbox below.

 - [ ] <!-- rebase-branch=renovate/nginxincnginx-unprivileged-image -->[chore(deps): update nginxinc/nginx-unprivileged:1.31-alpine docker digest to b54ac35](../pull/1450)
 - [ ] <!-- rebase-branch=renovate/projectdiscovery-nuclei-templates-10.x -->[chore(deps): update dependency projectdiscovery/nuclei-templates to v10.4.9](../pull/1454)
 - [ ] <!-- rebase-branch=renovate/python-minorpatch -->[chore(deps): update python minor/patch](../pull/1457) (`boto3`, `ruff`)
 - [ ] <!-- rebase-branch=renovate/frontend-minorpatch -->[chore(deps): update frontend minor/patch](../pull/1448) (`@sentry/react`, `@vitest/coverage-v8`, `knip`, `prettier`, `react-router-dom`, `vitest`)
 - [ ] <!-- rebase-all-open-prs -->**Click on this checkbox to rebase all open PRs at once**

## Detected Dependencies

<details><summary>asdf (1)</summary>
<blockquote>

<details><summary>src/frontend/.tool-versions (1)</summary>

 - `node 25.9.0`

</details>

</blockquote>
</details>

<details><summary>docker-compose (5)</summary>
<blockquote>

<details><summary>docker-compose.e2e.ci.yml</summary>


</details>

<details><summary>docker-compose.e2e.yml (5)</summary>

 - `arangodb 3.12@sha256:39bbca489179ea03f2b24b7ea4e4c4cb5258f6474f8c1c4d9bd65f7cd6d211a5`
 - `valkey/valkey 9-alpine@sha256:a0dbf4c1d5708782907c10e2c72deff317518518b5288a58416981d9db95d30b`
 - `timescale/timescaledb 2.30.0-pg16@sha256:75d58b53f3337a6babd3a1cce5e503f2300bdede62dd7d743651deb1a95b6d76`
 - `selenium/hub 4.48@sha256:d47c27474cb4cf356afa0a20c8eed8c3cf3a25c1b8e375357e6a0911e374d1da`
 - `selenium/node-chrome 152.0@sha256:5ac71fd8dd1ef5fb90ff38d01a6040185c3d16481479f96fdc888dbbed18a96a`

</details>

<details><summary>docker-compose.release.yml (8)</summary>

 - `arangodb 3.12@sha256:39bbca489179ea03f2b24b7ea4e4c4cb5258f6474f8c1c4d9bd65f7cd6d211a5`
 - `valkey/valkey 9-alpine@sha256:a0dbf4c1d5708782907c10e2c72deff317518518b5288a58416981d9db95d30b`
 - `ollama/ollama latest@sha256:0c0a83210471fb50226bcdc2d6611d20ab13ae87e024cc304c94a6a5765c5e65`
 - `timescale/timescaledb 2.30.0-pg16@sha256:75d58b53f3337a6babd3a1cce5e503f2300bdede62dd7d743651deb1a95b6d76`
 - `ghcr.io/nolte/kamerplanter-backend __VERSION__`
 - `ghcr.io/nolte/kamerplanter-backend __VERSION__`
 - `ghcr.io/nolte/kamerplanter-backend __VERSION__`
 - `ghcr.io/nolte/kamerplanter-frontend __VERSION__`

</details>

<details><summary>docker-compose.security.override.yml</summary>


</details>

<details><summary>docker-compose.yml (4)</summary>

 - `arangodb 3.12@sha256:39bbca489179ea03f2b24b7ea4e4c4cb5258f6474f8c1c4d9bd65f7cd6d211a5`
 - `valkey/valkey 9-alpine@sha256:a0dbf4c1d5708782907c10e2c72deff317518518b5288a58416981d9db95d30b`
 - `ollama/ollama latest@sha256:0c0a83210471fb50226bcdc2d6611d20ab13ae87e024cc304c94a6a5765c5e65`
 - `timescale/timescaledb 2.30.0-pg16@sha256:75d58b53f3337a6babd3a1cce5e503f2300bdede62dd7d743651deb1a95b6d76`

</details>

</blockquote>
</details>

<details><summary>dockerfile (9)</summary>
<blockquote>

<details><summary>docker/embedding-service/Dockerfile (6)</summary>

 - `python 3.14-slim@sha256:cad9a2c871761c413caa6fdd6441c783451e740a48aaeba60ae62a8b53525ef6`
 - `huggingface_hub unknown version`
 - `huggingface_hub unknown version`
 - `huggingface_hub unknown version`
 - `huggingface_hub unknown version`
 - `python 3.14-slim@sha256:cad9a2c871761c413caa6fdd6441c783451e740a48aaeba60ae62a8b53525ef6`

</details>

<details><summary>docker/knowledge/Dockerfile (1)</summary>

 - `busybox 1.38.0@sha256:dc2d74b28e4cf8984fa52af1f39bc7c3d9c73760b41a74d629f5d11b1ab28616`

</details>

<details><summary>docker/reranker-service/Dockerfile (4)</summary>

 - `python 3.14-slim@sha256:cad9a2c871761c413caa6fdd6441c783451e740a48aaeba60ae62a8b53525ef6`
 - `optimum.onnxruntime unknown version`
 - `optimum.onnxruntime unknown version`
 - `python 3.14-slim@sha256:cad9a2c871761c413caa6fdd6441c783451e740a48aaeba60ae62a8b53525ef6`

</details>

<details><summary>docker/vectordb/Dockerfile (1)</summary>

 - `postgres 18-bookworm@sha256:1c59e2c3c818eaa0f0628f695b36e7c9e362d6b219b36a54a32df645cbd7e1af`

</details>

<details><summary>src/backend/Dockerfile (2)</summary>

 - `python 3.14-slim@sha256:cad9a2c871761c413caa6fdd6441c783451e740a48aaeba60ae62a8b53525ef6`
 - `ghcr.io/astral-sh/uv 0.12.15@sha256:62f8c047d0a0e9ece6b53fc63df902585a67a47a7f318ddec4a37db586edc8e3`

</details>

<details><summary>src/frontend/Dockerfile (2)</summary>

 - `node 24-alpine@sha256:50c8e8ca1d27439048670df5883f32d57cf81cff6233222c893fd0d9884cbd81`
 - `nginxinc/nginx-unprivileged 1.31-alpine@sha256:19c132c9ab02d3b783f478743dafc7a7f42e27aa7d2bdcbec1bb1128ca8f2a07` → [Updates: `1.31-alpine`]

</details>

<details><summary>src/inference-service/Dockerfile (2)</summary>

 - `python 3.14-slim@sha256:cad9a2c871761c413caa6fdd6441c783451e740a48aaeba60ae62a8b53525ef6`
 - `python 3.14-slim@sha256:cad9a2c871761c413caa6fdd6441c783451e740a48aaeba60ae62a8b53525ef6`

</details>

<details><summary>src/knowledge-service/Dockerfile (1)</summary>

 - `python 3.14-slim@sha256:cad9a2c871761c413caa6fdd6441c783451e740a48aaeba60ae62a8b53525ef6`

</details>

<details><summary>tests/e2e/Dockerfile (3)</summary>

 - `node 22-slim@sha256:48e4b67d85f87bd551df43704e24d252f56cc5f8e9718841aace50f19948f0f9`
 - `python 3.14-slim@sha256:caaf356f40667c496d405780745b9ac25771c189a51dfcc42430d531ea09f8a2`
 - `ghcr.io/astral-sh/uv 0.12.15@sha256:62f8c047d0a0e9ece6b53fc63df902585a67a47a7f318ddec4a37db586edc8e3`

</details>

</blockquote>
</details>

<details><summary>github-actions (24)</summary>
<blockquote>

<details><summary>.github/workflows/api-docs.yml (4)</summary>

 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `actions/setup-python v7.0.0@5fda3b95a4ea91299a34e894583c3862153e4b97`
 - `actions/upload-artifact v7.0.1@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`
 - `python 3.14`

</details>

<details><summary>.github/workflows/automerge.yaml (1)</summary>

 - `nolte/gh-plumbing v2.1.0@3fccbb333146cd2a65902afd7394db870ae6a978`

</details>

<details><summary>.github/workflows/backend-guards.yml (3)</summary>

 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `actions/setup-python v7.0.0@5fda3b95a4ea91299a34e894583c3862153e4b97`
 - `python 3.14`

</details>

<details><summary>.github/workflows/backend.yml (15)</summary>

 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `actions/setup-python v7.0.0@5fda3b95a4ea91299a34e894583c3862153e4b97`
 - `go-task/setup-task v2.2.0@a00fbb05ce67b35648be3c78cbc9fd85354c757e`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `actions/setup-python v7.0.0@5fda3b95a4ea91299a34e894583c3862153e4b97`
 - `go-task/setup-task v2.2.0@a00fbb05ce67b35648be3c78cbc9fd85354c757e`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `actions/setup-python v7.0.0@5fda3b95a4ea91299a34e894583c3862153e4b97`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `actions/setup-python v7.0.0@5fda3b95a4ea91299a34e894583c3862153e4b97`
 - `nolte/gh-plumbing v2.1.0@3fccbb333146cd2a65902afd7394db870ae6a978`
 - `python ${{ matrix.python-version }}`
 - `python 3.14`
 - `python 3.14`
 - `python 3.14`

</details>

<details><summary>.github/workflows/build-static-tests.yaml (3)</summary>

 - `nolte/gh-plumbing v2.1.0@3fccbb333146cd2a65902afd7394db870ae6a978`
 - `nolte/gh-plumbing v2.1.0@3fccbb333146cd2a65902afd7394db870ae6a978`
 - `nolte/gh-plumbing v2.1.0@3fccbb333146cd2a65902afd7394db870ae6a978`

</details>

<details><summary>.github/workflows/delivery-run-alert.yml (2)</summary>

 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `actions/github-script v9.0.0@3a2844b7e9c422d3c10d287c895573f7108da1b3`

</details>

<details><summary>.github/workflows/docker-lint-build.yml (24)</summary>

 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `dorny/paths-filter v4.0.3@ceb8a2b8f2d89434be7ff52d3de7ec3738c5cc9d`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `docker/setup-buildx-action v4.4.1@f87e5991a6d7451dcb8d9637bfbc97413f497069`
 - `docker/build-push-action v7.4.0@c3c9e263c25d99ce0380d002d59b67737d91b0dc`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `docker/setup-buildx-action v4.4.1@f87e5991a6d7451dcb8d9637bfbc97413f497069`
 - `docker/build-push-action v7.4.0@c3c9e263c25d99ce0380d002d59b67737d91b0dc`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `docker/setup-buildx-action v4.4.1@f87e5991a6d7451dcb8d9637bfbc97413f497069`
 - `docker/build-push-action v7.4.0@c3c9e263c25d99ce0380d002d59b67737d91b0dc`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `docker/setup-buildx-action v4.4.1@f87e5991a6d7451dcb8d9637bfbc97413f497069`
 - `docker/build-push-action v7.4.0@c3c9e263c25d99ce0380d002d59b67737d91b0dc`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `docker/setup-buildx-action v4.4.1@f87e5991a6d7451dcb8d9637bfbc97413f497069`
 - `docker/build-push-action v7.4.0@c3c9e263c25d99ce0380d002d59b67737d91b0dc`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `docker/setup-buildx-action v4.4.1@f87e5991a6d7451dcb8d9637bfbc97413f497069`
 - `docker/build-push-action v7.4.0@c3c9e263c25d99ce0380d002d59b67737d91b0dc`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `docker/setup-buildx-action v4.4.1@f87e5991a6d7451dcb8d9637bfbc97413f497069`
 - `docker/build-push-action v7.4.0@c3c9e263c25d99ce0380d002d59b67737d91b0dc`

</details>

<details><summary>.github/workflows/docker-publish.yml (55)</summary>

 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `dorny/paths-filter v4.0.3@ceb8a2b8f2d89434be7ff52d3de7ec3738c5cc9d`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `docker/setup-buildx-action v4.4.1@f87e5991a6d7451dcb8d9637bfbc97413f497069`
 - `docker/login-action v4.6.0@dbcb813823bdd20940b903addbd779551569679f`
 - `docker/metadata-action v6.2.0@dc802804100637a589fabce1cb79ff13a1411302`
 - `docker/build-push-action v7.4.0@c3c9e263c25d99ce0380d002d59b67737d91b0dc`
 - `actions/attest-build-provenance v4.2.2@4d101475d8b20a2381f78447822ac1eab6504dd8`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `docker/setup-buildx-action v4.4.1@f87e5991a6d7451dcb8d9637bfbc97413f497069`
 - `docker/login-action v4.6.0@dbcb813823bdd20940b903addbd779551569679f`
 - `docker/metadata-action v6.2.0@dc802804100637a589fabce1cb79ff13a1411302`
 - `docker/build-push-action v7.4.0@c3c9e263c25d99ce0380d002d59b67737d91b0dc`
 - `actions/attest-build-provenance v4.2.2@4d101475d8b20a2381f78447822ac1eab6504dd8`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `docker/setup-buildx-action v4.4.1@f87e5991a6d7451dcb8d9637bfbc97413f497069`
 - `docker/login-action v4.6.0@dbcb813823bdd20940b903addbd779551569679f`
 - `docker/metadata-action v6.2.0@dc802804100637a589fabce1cb79ff13a1411302`
 - `docker/build-push-action v7.4.0@c3c9e263c25d99ce0380d002d59b67737d91b0dc`
 - `actions/attest-build-provenance v4.2.2@4d101475d8b20a2381f78447822ac1eab6504dd8`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `docker/setup-buildx-action v4.4.1@f87e5991a6d7451dcb8d9637bfbc97413f497069`
 - `docker/login-action v4.6.0@dbcb813823bdd20940b903addbd779551569679f`
 - `docker/metadata-action v6.2.0@dc802804100637a589fabce1cb79ff13a1411302`
 - `docker/build-push-action v7.4.0@c3c9e263c25d99ce0380d002d59b67737d91b0dc`
 - `actions/attest-build-provenance v4.2.2@4d101475d8b20a2381f78447822ac1eab6504dd8`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `docker/setup-buildx-action v4.4.1@f87e5991a6d7451dcb8d9637bfbc97413f497069`
 - `docker/login-action v4.6.0@dbcb813823bdd20940b903addbd779551569679f`
 - `docker/metadata-action v6.2.0@dc802804100637a589fabce1cb79ff13a1411302`
 - `docker/build-push-action v7.4.0@c3c9e263c25d99ce0380d002d59b67737d91b0dc`
 - `actions/attest-build-provenance v4.2.2@4d101475d8b20a2381f78447822ac1eab6504dd8`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `docker/setup-buildx-action v4.4.1@f87e5991a6d7451dcb8d9637bfbc97413f497069`
 - `docker/login-action v4.6.0@dbcb813823bdd20940b903addbd779551569679f`
 - `docker/metadata-action v6.2.0@dc802804100637a589fabce1cb79ff13a1411302`
 - `docker/build-push-action v7.4.0@c3c9e263c25d99ce0380d002d59b67737d91b0dc`
 - `actions/attest-build-provenance v4.2.2@4d101475d8b20a2381f78447822ac1eab6504dd8`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `docker/setup-buildx-action v4.4.1@f87e5991a6d7451dcb8d9637bfbc97413f497069`
 - `docker/login-action v4.6.0@dbcb813823bdd20940b903addbd779551569679f`
 - `docker/metadata-action v6.2.0@dc802804100637a589fabce1cb79ff13a1411302`
 - `docker/build-push-action v7.4.0@c3c9e263c25d99ce0380d002d59b67737d91b0dc`
 - `actions/attest-build-provenance v4.2.2@4d101475d8b20a2381f78447822ac1eab6504dd8`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `docker/setup-buildx-action v4.4.1@f87e5991a6d7451dcb8d9637bfbc97413f497069`
 - `docker/login-action v4.6.0@dbcb813823bdd20940b903addbd779551569679f`
 - `docker/metadata-action v6.2.0@dc802804100637a589fabce1cb79ff13a1411302`
 - `docker/build-push-action v7.4.0@c3c9e263c25d99ce0380d002d59b67737d91b0dc`
 - `actions/attest-build-provenance v4.2.2@4d101475d8b20a2381f78447822ac1eab6504dd8`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `azure/setup-helm v5.0.1@9bc31f4ebc9c6b171d7bfbaa5d006ae7abdb4310`
 - `docker/login-action v4.6.0@dbcb813823bdd20940b903addbd779551569679f`
 - `actions/attest-build-provenance v4.2.2@4d101475d8b20a2381f78447822ac1eab6504dd8`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`

</details>

<details><summary>.github/workflows/e2e-nightly.yml (6)</summary>

 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `docker/setup-buildx-action v4.4.1@f87e5991a6d7451dcb8d9637bfbc97413f497069`
 - `crazy-max/ghaction-github-runtime v4.0.0@04d248b84655b509d8c44dc1d6f990c879747487`
 - `dorny/test-reporter v3.0.0@a43b3a5f7366b97d083190328d2c652e1a8b6aa2`
 - `actions/upload-artifact v7.0.1@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`

</details>

<details><summary>.github/workflows/e2e-smoke.yml (7)</summary>

 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `dorny/paths-filter v4.0.3@ceb8a2b8f2d89434be7ff52d3de7ec3738c5cc9d`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `docker/setup-buildx-action v4.4.1@f87e5991a6d7451dcb8d9637bfbc97413f497069`
 - `crazy-max/ghaction-github-runtime v4.0.0@04d248b84655b509d8c44dc1d6f990c879747487`
 - `dorny/test-reporter v3.0.0@a43b3a5f7366b97d083190328d2c652e1a8b6aa2`
 - `actions/upload-artifact v7.0.1@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`

</details>

<details><summary>.github/workflows/frontend.yml (28)</summary>

 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `dorny/paths-filter v4.0.3@ceb8a2b8f2d89434be7ff52d3de7ec3738c5cc9d`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `actions/setup-node v7.0.0@820762786026740c76f36085b0efc47a31fe5020`
 - `go-task/setup-task v2.2.0@a00fbb05ce67b35648be3c78cbc9fd85354c757e`
 - `actions/upload-artifact v7.0.1@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`
 - `nolte/gh-plumbing v2.1.0@3fccbb333146cd2a65902afd7394db870ae6a978`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `actions/setup-node v7.0.0@820762786026740c76f36085b0efc47a31fe5020`
 - `actions/upload-artifact v7.0.1@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `actions/setup-node v7.0.0@820762786026740c76f36085b0efc47a31fe5020`
 - `actions/upload-artifact v7.0.1@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `actions/setup-node v7.0.0@820762786026740c76f36085b0efc47a31fe5020`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `actions/setup-node v7.0.0@820762786026740c76f36085b0efc47a31fe5020`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `actions/setup-node v7.0.0@820762786026740c76f36085b0efc47a31fe5020`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `actions/setup-node v7.0.0@820762786026740c76f36085b0efc47a31fe5020`
 - `node ${{ matrix.node-version }}`
 - `node 24`
 - `node 24`
 - `node 24`
 - `node 24`
 - `node 24`
 - `node 24`

</details>

<details><summary>.github/workflows/release-assets-complete.yml (2)</summary>

 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `actions/github-script v9.0.0@3a2844b7e9c422d3c10d287c895573f7108da1b3`

</details>

<details><summary>.github/workflows/release-cd-deliver-docs.yml (1)</summary>

 - `nolte/gh-plumbing v2.1.0@3fccbb333146cd2a65902afd7394db870ae6a978`

</details>

<details><summary>.github/workflows/release-cd-refresh-master.yml (1)</summary>

 - `nolte/gh-plumbing v2.1.0@3fccbb333146cd2a65902afd7394db870ae6a978`

</details>

<details><summary>.github/workflows/release-drafter.yml (1)</summary>

 - `nolte/gh-plumbing v2.1.0@3fccbb333146cd2a65902afd7394db870ae6a978`

</details>

<details><summary>.github/workflows/release-lag.yml (2)</summary>

 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `actions/github-script v9.0.0@3a2844b7e9c422d3c10d287c895573f7108da1b3`

</details>

<details><summary>.github/workflows/release-publish.yml (4)</summary>

 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `actions/setup-python v7.0.0@5fda3b95a4ea91299a34e894583c3862153e4b97`
 - `nolte/gh-plumbing v2.1.0@3fccbb333146cd2a65902afd7394db870ae6a978`
 - `python 3.14`

</details>

<details><summary>.github/workflows/security-nuclei-nightly.yml (5)</summary>

 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `projectdiscovery/nuclei-action v3.1.1@cc153d0541e1adf8a42bbe31c0a4fb2376147538`
 - `github/codeql-action v4.38.0@b96794f015dfd88f77b49b1c93e0fa7110f94c63`
 - `actions/upload-artifact v7.0.1@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`
 - `actions/github-script v9.0.0@3a2844b7e9c422d3c10d287c895573f7108da1b3`

</details>

<details><summary>.github/workflows/security-nuclei-postmerge.yml (6)</summary>

 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `projectdiscovery/nuclei-action v3.1.1@cc153d0541e1adf8a42bbe31c0a4fb2376147538`
 - `github/codeql-action v4.38.0@b96794f015dfd88f77b49b1c93e0fa7110f94c63`
 - `github/codeql-action v4.38.0@b96794f015dfd88f77b49b1c93e0fa7110f94c63`
 - `actions/upload-artifact v7.0.1@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`
 - `actions/github-script v9.0.0@3a2844b7e9c422d3c10d287c895573f7108da1b3`

</details>

<details><summary>.github/workflows/security-nuclei-templates.yml (2)</summary>

 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `projectdiscovery/nuclei-action v3.1.1@cc153d0541e1adf8a42bbe31c0a4fb2376147538`

</details>

<details><summary>.github/workflows/security-zap-nightly.yml (2)</summary>

 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `actions/upload-artifact v7.0.1@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`

</details>

<details><summary>.github/workflows/security-zap-postmerge.yml (3)</summary>

 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `actions/upload-artifact v7.0.1@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`
 - `actions/github-script v9.0.0@3a2844b7e9c422d3c10d287c895573f7108da1b3`

</details>

<details><summary>.github/workflows/side-services.yml (12)</summary>

 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `actions/setup-python v7.0.0@5fda3b95a4ea91299a34e894583c3862153e4b97`
 - `go-task/setup-task v2.2.0@a00fbb05ce67b35648be3c78cbc9fd85354c757e`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `actions/setup-python v7.0.0@5fda3b95a4ea91299a34e894583c3862153e4b97`
 - `go-task/setup-task v2.2.0@a00fbb05ce67b35648be3c78cbc9fd85354c757e`
 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `actions/setup-python v7.0.0@5fda3b95a4ea91299a34e894583c3862153e4b97`
 - `go-task/setup-task v2.2.0@a00fbb05ce67b35648be3c78cbc9fd85354c757e`
 - `python 3.14`
 - `python 3.14`
 - `python 3.14`

</details>

<details><summary>.github/workflows/skaffold-verify.yml (4)</summary>

 - `actions/checkout v7.0.1@3d3c42e5aac5ba805825da76410c181273ba90b1`
 - `azure/setup-helm v5.0.1@9bc31f4ebc9c6b171d7bfbaa5d006ae7abdb4310`
 - `hiberbee/github-action-skaffold 1.27.0@e3f5dd5659610cb792c6cf32daaa797ea6d89842`
 - `actions/upload-artifact v7.0.1@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a`

</details>

</blockquote>
</details>

<details><summary>helm-values (4)</summary>
<blockquote>

<details><summary>helm/kamerplanter/values-dev-ki.yaml</summary>


</details>

<details><summary>helm/kamerplanter/values-dev-recognition.yaml</summary>


</details>

<details><summary>helm/kamerplanter/values-dev.yaml (1)</summary>

 - `timescale/timescaledb 2.30.0-pg16`

</details>

<details><summary>helm/kamerplanter/values.yaml (1)</summary>

 - `arangodb 3.12.11`

</details>

</blockquote>
</details>

<details><summary>helmv3 (1)</summary>
<blockquote>

<details><summary>helm/kamerplanter/Chart.yaml (3)</summary>

 - `common 5.2.0`
 - `valkey 0.12.0`
 - `ollama 1.81.0`

</details>

</blockquote>
</details>

<details><summary>npm (2)</summary>
<blockquote>

<details><summary>src/frontend/package.json (48)</summary>

 - `@emotion/react ^11.14.0`
 - `@emotion/styled ^11.14.1`
 - `@hookform/resolvers ^5.2.2`
 - `@mui/icons-material ^9.0.0`
 - `@mui/material ^9.0.0`
 - `@mui/x-date-pickers ^9.0.0`
 - `@mui/x-tree-view ^9.0.0`
 - `@reduxjs/toolkit ^2.11.2`
 - `@sentry/react ^10.68.0` → [Updates: `^10.68.0`]
 - `axios ^1.14.0`
 - `dayjs ^1.11.20`
 - `i18next ^26.0.1`
 - `i18next-browser-languagedetector ^8.2.1`
 - `notistack ^3.0.2`
 - `qrcode.react ^4.2.0`
 - `react ^19.2.4`
 - `react-dom ^19.2.4`
 - `react-grid-layout ^2.0.0`
 - `react-hook-form ^7.72.0`
 - `react-i18next ^17.0.1`
 - `react-redux ^9.2.0`
 - `react-router-dom ^7.13.2` → [Updates: `^7.13.2`]
 - `recharts ^3.8.1`
 - `zod ^4.3.6`
 - `@eslint/js ^10.0.0`
 - `@lhci/cli ^0.15.1`
 - `@testing-library/jest-dom ^7.0.0`
 - `@testing-library/react ^16.3.2`
 - `@testing-library/user-event ^14.6.1`
 - `@types/react ^19.2.14`
 - `@types/react-dom ^19.2.3`
 - `@types/react-grid-layout ^2.0.0`
 - `@vitejs/plugin-react ^6.0.1`
 - `@vitest/coverage-v8 ^5.0.0` → [Updates: `^5.0.0`]
 - `eslint ^10.0.0`
 - `eslint-config-prettier ^10.1.8`
 - `eslint-plugin-react-hooks ^7.0.1`
 - `globals ^17.4.0`
 - `jsdom ^29.0.1` → [Updates: `^30.0.0`]
 - `knip 6.35.1` → [Updates: `6.36.0`]
 - `msw ^2.12.14`
 - `prettier ^3.8.1` → [Updates: `^3.8.1`]
 - `rollup-plugin-visualizer ^7.0.0`
 - `typescript ~6.0.0`
 - `typescript-eslint ^8.57.2`
 - `vite ^8.0.3`
 - `vitest ^5.0.0` → [Updates: `^5.0.0`]
 - `vitest-axe ^1.0.0-pre.5`

</details>

<details><summary>tests/e2e/package.json (1)</summary>

 - `axe-core ^4.11.1`

</details>

</blockquote>
</details>

<details><summary>pep621 (8)</summary>
<blockquote>

<details><summary>src/backend/pyproject.toml (42)</summary>

 - `python >=3.14`
 - `fastapi >=0.115.0,<1.0.0`
 - `uvicorn >=0.32.0,<1.0.0`
 - `pydantic >=2.10.0,<3.0.0`
 - `pydantic-settings >=2.7.0,<3.0.0`
 - `python-arango >=8.1.0,<9.0.0`
 - `redis >=5.2.0,<9.0.0`
 - `celery >=5.4.0,<6.0.0`
 - `structlog >=24.4.0,<27.0.0`
 - `httpx >=0.28.0,<1.0.0`
 - `markdownify >=0.14.0,<2.0.0`
 - `astral >=3.2,<4.0.0`
 - `authlib >=1.3.0,<2.0.0`
 - `bcrypt >=4.0,<6.0.0`
 - `slowapi >=0.1.9,<1.0.0`
 - `cryptography >=50,<50.1`
 - `python-multipart >=0.0.9,<1.0.0`
 - `pyyaml >=6.0,<7.0.0`
 - `croniter >=2.0,<7.0.0`
 - `python-dateutil >=2.9,<3.0.0`
 - `psycopg >=3.2.0,<4.0.0`
 - `pgvector >=0.3.6,<1.0.0`
 - `jinja2 >=3.1,<4.0.0`
 - `weasyprint >=70,<71.0.0`
 - `qrcode >=8.0,<9.0.0`
 - `zeroconf >=0.131.0,<1.0.0`
 - `pywebpush >=2.0.0,<3.0.0`
 - `boto3 >=1.35,<2.0.0` → [Updates: `>=1.35,<2.0.0`]
 - `pillow >=11.0,<13.0.0`
 - `aquacropeto >=0.1.1,<1.0.0`
 - `sentry-sdk >=2.20.0,<3.0.0`
 - `pytest >=8.3.0,<10.0.0`
 - `pytest-asyncio >=0.24.0,<2.0.0`
 - `pytest-cov >=6.0.0,<8.0.0`
 - `freezegun >=1.5.0,<2.0.0`
 - `ruff >=0.8.0,<1.0.0` → [Updates: `>=0.8.0,<1.0.0`]
 - `mypy >=1.13.0,<3.0.0`
 - `black >=24.10.0,<27.0.0`
 - `moto >=5.0,<6.0.0`
 - `jsonschema >=4.23.0,<5.0.0`
 - `referencing >=0.35.0,<1.0.0`
 - `setuptools >=75.0`

</details>

<details><summary>src/inference-service/pyproject.toml (17)</summary>

 - `fastapi >=0.115.0`
 - `uvicorn >=0.32.0`
 - `python-multipart >=0.0.18`
 - `onnxruntime >=1.20.0`
 - `numpy >=2.0.0`
 - `pillow >=11.0.0`
 - `psycopg >=3.2.0`
 - `psycopg-pool >=3.2.0`
 - `pydantic >=2.10.0`
 - `pydantic-settings >=2.7.0`
 - `structlog >=24.0.0`
 - `plantcv >=4.0`
 - `pytest >=8.0`
 - `pytest-asyncio >=0.24`
 - `ruff >=0.8.0`
 - `mypy >=1.13.0`
 - `httpx >=0.28.0`

</details>
<details><summary>src/knowledge-service/pyproject.toml (13)</summary>

 - `fastapi >=0.115.0`
 - `uvicorn >=0.32.0`
 - `httpx >=0.28.0`
 - `psycopg >=3.2.0`
 - `psycopg-pool >=3.2.0`
 - `pydantic >=2.10.0`
 - `pydantic-settings >=2.7.0`
 - `pyyaml >=6.0`
 - `structlog >=24.0.0`
 - `pytest >=8.0`
 - `pytest-asyncio >=0.24`
 - `ruff >=0.8.0`
 - `mypy >=1.13.0`

</details>
<details><summary>docker/embedding-service/pyproject.toml (5)</summary>

 - `fastapi >=0.115.0`
 - `uvicorn >=0.32.0`
 - `onnxruntime >=1.20.0`
 - `transformers >=4.46.0`
 - `huggingface-hub >=0.26.0`

</details>

<details><summary>docker/reranker-service/pyproject.toml (6)</summary>

 - `fastapi >=0.115.0`
 - `uvicorn >=0.32.0`
 - `onnxruntime >=1.20.0`
 - `transformers >=4.46.0`
 - `optimum >=1.23.0`
 - `sentencepiece >=0.2.0`

</details>

<details><summary>src/libs/kp_vectordb/pyproject.toml (6)</summary>

 - `psycopg >=3.2.0`
 - `psycopg-pool >=3.2.0`
 - `structlog >=24.0.0`
 - `pytest >=8.0`
 - `ruff >=0.8.0`
 - `mypy >=1.13.0`

</details>

<details><summary>src/libs/kp_errortracking/pyproject.toml (4)</summary>

 - `pytest >=8.0`
 - `ruff >=0.8.0`
 - `mypy >=1.13.0`
 - `sentry-sdk >=2.20.0`

</details>

<details><summary>tests/e2e/pyproject.toml (5)</summary>

 - `selenium >=4.25.0,<5`
 - `webdriver-manager >=4.0.0`
 - `pytest >=8.3.0`
 - `pytest-bdd >=8.1.0`
 - `pytest-xdist >=3.5.0`

</details>

</blockquote>
</details>

<details><summary>pip_requirements (2)</summary>
<blockquote>



<details><summary>docs/requirements.txt (53)</summary>

 - `babel ==2.17.0`
 - `backrefs ==8.0`
 - `bracex ==3.0.1`
 - `certifi ==2026.7.22`
 - `charset-normalizer ==3.5.1`
 - `click ==8.5.0`
 - `colorama ==0.4.6`
 - `csscompressor ==0.9.5`
 - `ghp-import ==2.1.0`
 - `gitdb ==4.0.12`
 - `gitpython ==3.1.62`
 - `griffelib ==2.3.0`
 - `htmlmin2 ==0.1.13`
 - `idna ==3.20`
 - `jinja2 ==3.1.6`
 - `jsmin ==3.0.1`
 - `markdown ==3.10.3`
 - `markupsafe ==3.0.3`
 - `mergedeep ==1.3.4`
 - `mike ==2.2.0`
 - `mkdocs ==1.6.1`
 - `mkdocs-autorefs ==1.4.4`
 - `mkdocs-awesome-pages-plugin ==2.10.1`
 - `mkdocs-get-deps ==0.2.2`
 - `mkdocs-git-revision-date-localized-plugin ==1.6.0`
 - `mkdocs-literate-nav ==0.6.3`
 - `mkdocs-material ==9.7.7`
 - `mkdocs-material-extensions ==1.3.1`
 - `mkdocs-minify-plugin ==0.8.0`
 - `mkdocs-redirects ==1.2.3`
 - `mkdocs-static-i18n ==1.3.1`
 - `mkdocstrings ==1.0.6`
 - `mkdocstrings-python ==2.0.8`
 - `natsort ==8.4.0`
 - `packaging ==26.3`
 - `paginate ==0.5.7`
 - `pathspec ==1.1.1`
 - `platformdirs ==4.11.11`
 - `properdocs ==1.6.7`
 - `pygments ==2.21.0`
 - `pymdown-extensions ==12.0.1`
 - `pyparsing ==3.3.2`
 - `python-dateutil ==2.9.0.post0`
 - `pyyaml ==6.0.3`
 - `pyyaml-env-tag ==1.1`
 - `requests ==2.34.2`
 - `six ==1.17.0`
 - `smmap ==5.0.3`
 - `tzdata ==2026.4`
 - `urllib3 ==2.8.0`
 - `verspec ==0.1.0`
 - `watchdog ==6.0.0`
 - `wcmatch ==11.0.1`

</details>



<details><summary>tools/rag-eval/requirements.txt (3)</summary>

 - `httpx >=0.28.0`
 - `psycopg >=3.2.0`
 - `pyyaml >=6.0`

</details>

</blockquote>
</details>

<details><summary>pre-commit (1)</summary>
<blockquote>

<details><summary>.pre-commit-config.yaml (20)</summary>

 - `pre-commit/pre-commit-hooks v6.0.0`
 - `ruff >=0.15.0`
 - `ruff >=0.15.0`
 - `selenium >=4.25.0,<5`
 - `pytest >=8.3.0`
 - `PyYAML >=6.0`
 - `PyYAML >=6.0`
 - `PyYAML >=6.0`
 - `rhysd/actionlint v1.7.12`
 - `koalaman/shellcheck-precommit v0.11.0`
 - `PyYAML >=6.0`
 - `PyYAML >=6.0`
 - `python-jsonschema/check-jsonschema 0.38.0`
 - `ruff >=0.15.0`
 - `ruff >=0.15.0`
 - `mypy >=1.13.0`
 - `mypy >=1.13.0`
 - `mypy >=1.13.0`
 - `mypy >=1.13.0`
 - `PyYAML >=6.0`

</details>

</blockquote>
</details>

<details><summary>regex (9)</summary>
<blockquote>

<details><summary>.github/renovate-pins.yaml (2)</summary>

 - `projectdiscovery/nuclei-templates v10.4.8` → [Updates: `v10.4.9`]
 - `projectdiscovery/nuclei v3.11.1`

</details>

<details><summary>.github/workflows/api-docs.yml (2)</summary>

 - `uv 0.12.15`
 - `@stoplight/spectral-cli 6.16.3`

</details>

<details><summary>.github/workflows/backend-guards.yml (1)</summary>

 - `uv 0.12.15`

</details>

<details><summary>.github/workflows/backend.yml (7)</summary>

 - `uv 0.12.15`
 - `uv 0.12.15`
 - `uv 0.12.15`
 - `pip-audit 2.10.1`
 - `uv 0.12.15`
 - `pip-licenses 5.5.5`
 - `uv 0.12.15`

</details>

<details><summary>.github/workflows/docker-lint-build.yml (1)</summary>

 - `ghcr.io/hadolint/hadolint v2.15.1@sha256:32dac94127fd60b7b7e3fbfc65e1383b9b5e25c9bfd7b8536de7a539fe68a12d`

</details>

<details><summary>.github/workflows/release-publish.yml (1)</summary>

 - `uv 0.12.15`

</details>

<details><summary>.vale.ini (1)</summary>

 - `nolte/vale-style v0.1.17`

</details>

<details><summary>src/backend/pyproject.toml (3)</summary>

 - `uv 0.12.15`
 - `setuptools 84.0.0`
 - `wheel 0.48.0`

</details>

<details><summary>tests/e2e/pyproject.toml (1)</summary>

 - `uv 0.12.15`

</details>

</blockquote>
</details>

<details><summary>renovate-config (1)</summary>
<blockquote>

<details><summary>renovate.json5 (1)</summary>

 - `nolte/gh-plumbing v2.1.0`

</details>

</blockquote>
</details>

---

- [ ] <!-- manual job -->Check this box to trigger a request for Renovate to run again on this repository
