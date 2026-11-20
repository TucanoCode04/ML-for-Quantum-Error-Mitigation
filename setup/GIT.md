# Working with git

Each group works on its own branch. Nobody pushes to `main`: code gets there through a pull request.

| Group                | Branch       |
|----------------------|--------------|
| Circuits & hardware  | `circuits`   |
| Simulation & ZNE     | `simulation` |
| Models               | `models`     |

## First time

```
git pull
git switch circuits
```

(or `simulation` / `models`, depending on your group)

## Every time you work

Start by getting what your teammate pushed:

```
git pull
```

When you finished something that works, save it and send it:

```
git add <files you changed>
git commit -m "short description of what you did"
git push
```

Commit often, with small commits. Don't add `tokens.json` or data files by accident (check with `git status` before committing).

## Pull request (when a part is ready for main)

1. Push your branch.
2. On GitHub, open the repo, click "Pull requests", then "New pull request".
3. Base: `main`, compare: your branch. Write two lines on what it does, then "Create pull request".
4. The coordinator reviews it and merges it. If changes are asked, just commit and push again on the same branch, the pull request updates by itself.

After the merge, don't delete the branch, keep working on it.

## Getting the other groups' work

When something new is merged into main, bring it into your branch:

```
git pull origin main
git push
```

If git says there is a conflict, don't panic and ask in the group chat.
