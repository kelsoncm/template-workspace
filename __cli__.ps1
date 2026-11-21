$nomeSemExtensao = (Get-Item $PSCommandPath).BaseName
uv run --script "$PSScriptRoot\$nomeSemExtensao" @args
