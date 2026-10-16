# Standalone runtime

Hermes Recall retains an operator CLI independent of Hermes. This interface uses a separate profile selected with `--home`; it does not perform native Hermes conversation capture. See [mcp.md](mcp.md) for installation and the optional stdio interface.

```sh
hermes-recall --home /path/to/separate-profile --help
hermes-recall --home /path/to/separate-profile init --existing use
hermes-recall --home /path/to/separate-profile status
hermes-recall --home /path/to/separate-profile add --text 'Example durable fact'
hermes-recall --home /path/to/separate-profile search --query 'durable fact'
```

Provide embedding configuration and credentials deliberately. Stop all other writers to the embedded destination before using this runtime. Maintenance file arguments are limited to the operator working directory; exports can contain sensitive memory text.
