## Summary

-

## Change Type

- [ ] Documentation
- [ ] Skill instructions or references
- [ ] Python helper/checker
- [ ] R helper/demo
- [ ] Examples or fixtures
- [ ] Rule/evidence update
- [ ] Journal profile or schema

## Redaction Checklist

- [ ] This PR contains no private manuscript text, unpublished results, author names, reviewer identities, submission IDs, or confidential journal correspondence.
- [ ] Any editor/reviewer comment has been paraphrased into a reusable formatting requirement.
- [ ] I am authorized to publish every contributed paraphrase; no original private correspondence is included.
- [ ] Non-official evidence is not presented as official Elsevier policy.

## Validation

- [ ] `pip install -r requirements-dev.txt`
- [ ] `python skills/elsevier-figure-style/scripts/check_environment.py`
- [ ] `pytest`
- [ ] `python skills/elsevier-figure-style/scripts/check_elsevier_figure_style.py --path examples/python --profile editor`
- [ ] `npx skills@1.5.15 add . --list`
- [ ] Metadata checker or demo generation, if relevant
