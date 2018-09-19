# HDX Styles

> Repo with HDX Common Styles 

## Technologies

- [**Gulp**](http://gulpjs.com)
- [**Html**](https://developer.mozilla.org/es/docs/HTML/HTML5) 
- [**Less**](http://lesscss.org) 
- [**Babel**](https://babeljs.io)
- [**JSHint**](http://jshint.com) 

# Using this repository in another/your repository
This repo is usually included as a subtree in other repositories. Follow the following steps to integrate/use it properly.

### Integrating the repository as a subtree in a new project or project that wasn't using it

1. Add a new origin

` git remote add -f hdx-styles https://github.com/OCHA-DAP/hdx-styles.git `

2. Add&pull the repo while squashing the previous commit from the hdx-style repo 

` git subtree add --prefix ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles hdx-styles master --squash `

### On a daily base, getting the latest changes from the repo inside the subtree

` git subtree pull --prefix src/hdx-styles hdx-styles master --squash `

e.g.
` git subtree pull --prefix ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles hdx-styles master --squash `

### Commiting changes inside the subtree
1. Please, do an individual commit for the changes inside the subtree.

`(commit something just on the subtree path)`

2. Push all the commits on the subtree back to the origin in <your-changes-branch>

` git subtree push --prefix src/hdx-styles hdx-styles <your-changes-branch> `

e.g.
` git subtree push --prefix ckanext-hdx_theme/ckanext/hdx_theme/hdx-styles hdx-styles feature/HDX-6096-freshness `

 

# License 

The code is available under the **MIT** license. 
