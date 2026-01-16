"""Tools package for EasyAirClaim MCP Server."""

from tools.health_tools import (
    health_check,
    get_database_stats,
    get_environment_info
)

from tools.customer_tools import (
    create_customer,
    get_customer,
    get_customer_by_email,
    list_customers,
    delete_customer
)

from tools.claim_tools import (
    create_claim,
    get_claim,
    list_claims,
    transition_claim_status,
    add_claim_note
)

from tools.file_tools import (
    list_claim_files,
    get_file_metadata,
    get_file_validation_status,
    approve_file,
    reject_file,
    delete_file,
    get_files_by_status
)

from tools.user_tools import (
    create_user,
    create_admin,
    get_user,
    get_user_by_email,
    list_users,
    update_user,
    delete_user,
    activate_user,
    deactivate_user,
    verify_user_email
)

from tools.dev_tools import (
    seed_realistic_data,
    create_test_scenario,
    reset_database,
    validate_data_integrity
)

__all__ = [
    # Health
    "health_check",
    "get_database_stats",
    "get_environment_info",
    
    # Customer
    "create_customer",
    "get_customer",
    "get_customer_by_email",
    "list_customers",
    "delete_customer",
    
    # Claim
    "create_claim",
    "get_claim",
    "list_claims",
    "transition_claim_status",
    "add_claim_note",
    
    # File
    "list_claim_files",
    "get_file_metadata",
    "get_file_validation_status",
    "approve_file",
    "reject_file",
    "delete_file",
    "get_files_by_status",
    
    # User
    "create_user",
    "create_admin",
    "get_user",
    "get_user_by_email",
    "list_users",
    "update_user",
    "delete_user",
    "activate_user",
    "deactivate_user",
    "verify_user_email",
    
    # Dev Tools
    "seed_realistic_data",
    "create_test_scenario",
    "reset_database",
    "validate_data_integrity",
]
