@Library('platform@main') _

// BUILD_TARGET: auto | all | gateway | auth-service | catalog-service | order-service | payment-worker | shop-web
// Central library: https://github.com/kevinram164/jenkins-shared-library

platformPipeline([
  project             : 'npd-shop',
  harborHost          : 'harbor-platform.apps.ocp01.npd.co',
  harborProject       : 'npd-shop',
  gitBranch           : 'main',
  gitRepoUrl          : 'https://github.com/kevinram164/npd-shop.git',
  gitopsValuesFile    : 'gitops/values-images.yaml',
  vaultAddr           : 'http://vault.vault.svc.cluster.local:8200',
  vaultRole           : 'jenkins-kaniko',
  vaultHarborPath     : 'npd-shop/harbor',
  vaultGithubPath     : 'platform/github',
  kanikoSkipTlsVerify : true,
])
