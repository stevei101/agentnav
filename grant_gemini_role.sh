#!/bin/bash
# Grant geminicodeassistmanagement.scmConnectionAdmin role to an identity
# Usage: ./grant_gemini_role.sh <identity-type> <identity-value>
# Example: ./grant_gemini_role.sh user user@example.com
# Example: ./grant_gemini_role.sh serviceAccount sa@project.iam.gserviceaccount.com

PROJECT_ID="$GCP_PROJECT_ID"
ROLE="geminicodeassistmanagement.scmConnectionAdmin"

if [ $# -lt 2 ]; then
    echo "Usage: $0 <identity-type> <identity-value>"
    echo "Identity types: user, serviceAccount, group"
    echo ""
    echo "Examples:"
    echo "  $0 user user@example.com"
    echo "  $0 serviceAccount my-sa@free-project-1249.iam.gserviceaccount.com"
    echo "  $0 group group@example.com"
    exit 1
fi

IDENTITY_TYPE=$1
IDENTITY_VALUE=$2

# Construct member string based on type
case $IDENTITY_TYPE in
    user)
        MEMBER="user:${IDENTITY_VALUE}"
        ;;
    serviceAccount)
        MEMBER="serviceAccount:${IDENTITY_VALUE}"
        ;;
    group)
        MEMBER="group:${IDENTITY_VALUE}"
        ;;
    *)
        echo "Error: Invalid identity type. Use: user, serviceAccount, or group"
        exit 1
        ;;
esac

echo "Granting role to: ${MEMBER}"
echo "Project: ${PROJECT_ID}"
echo "Role: ${ROLE}"
echo ""

# Try with roles/ prefix first (standard format)
echo "Attempting with roles/ prefix..."
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="${MEMBER}" \
    --role="roles/${ROLE}" \
    --condition=None 2>&1

if [ $? -ne 0 ]; then
    echo ""
    echo "Trying without roles/ prefix..."
    gcloud projects add-iam-policy-binding ${PROJECT_ID} \
        --member="${MEMBER}" \
        --role="${ROLE}" \
        --condition=None
fi

echo ""
echo "Done! Verifying..."
gcloud projects get-iam-policy ${PROJECT_ID} \
    --flatten="bindings[].members" \
    --filter="bindings.members:${MEMBER} AND bindings.role:${ROLE} OR bindings.role:roles/${ROLE}" \
    --format="table(bindings.role)"

