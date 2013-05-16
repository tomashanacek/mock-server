### Parameters

Represents a created repository, branch, or tag.

Hook name: `create`

:ref_type:string:required:branch

The object that was created: “repository”, “branch”, or “tag”

:ref:string:optional:123

The git ref (or null if only a repository was created).

:master_branch:string:optional:master

The name of the repository’s master branch.

:description:string:optional:bla bla

The repository’s current description.