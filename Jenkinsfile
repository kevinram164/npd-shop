@Library('platform@main') _

// BUILD_TARGET: auto | all | gateway | auth-service | catalog-service | order-service | payment-worker | shop-web
// Central library: https://github.com/kevinram164/jenkins-shared-library
// dev-k8s: Jenkins → npd-harbor.co → bump deploy/dev-k8s/values/values-images.yaml → ArgoCD

platformPipeline([
  project             : 'npd-shop',
  harborHost          : 'npd-harbor.co',
  harborProject       : 'npd-shop',
  gitBranch           : 'main',
  gitRepoUrl          : 'https://github.com/kevinram164/npd-shop.git',
  gitopsValuesFile    : 'deploy/dev-k8s/values/values-images.yaml',
  vaultAddr           : 'http://vault.vault.svc.cluster.local:8200',
  vaultRole           : 'jenkins-kaniko',
  vaultHarborPath     : 'npd-shop/harbor',
  vaultGithubPath     : 'platform/github',
  kanikoSkipTlsVerify : true,
  kanikoUseCache      : false,
])
