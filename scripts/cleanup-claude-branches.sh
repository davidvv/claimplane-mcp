#!/bin/bash

# Script to merge and cleanup Claude Code Web auto-generated branches
# Usage: ./scripts/cleanup-claude-branches.sh

set -e

echo "🔍 Finding Claude auto-generated branches..."

# Get all claude/* branches
CLAUDE_BRANCHES=$(git branch -r | grep 'origin/claude/' | sed 's/origin\///' | sed 's/^[[:space:]]*//')

if [ -z "$CLAUDE_BRANCHES" ]; then
    echo "✅ No Claude branches found to clean up!"
    exit 0
fi

echo "📋 Found the following branches:"
echo "$CLAUDE_BRANCHES"
echo ""

# Ask which branch to merge into
echo "Which branch do you want to merge these into?"
echo "1) UI"
echo "2) MVP"
echo "3) main"
read -p "Enter choice (1-3): " choice

case $choice in
    1) TARGET_BRANCH="UI" ;;
    2) TARGET_BRANCH="MVP" ;;
    3) TARGET_BRANCH="main" ;;
    *) echo "❌ Invalid choice"; exit 1 ;;
esac

echo ""
echo "🎯 Target branch: $TARGET_BRANCH"
echo ""

# Checkout target branch
git checkout $TARGET_BRANCH
git pull origin $TARGET_BRANCH

# Merge each Claude branch
for branch in $CLAUDE_BRANCHES; do
    echo "🔀 Merging $branch..."
    git merge --no-ff $branch -m "merge: absorb changes from auto-generated branch $branch"

    # Delete local branch if it exists
    LOCAL_BRANCH=$(echo $branch | sed 's/^origin\///')
    if git show-ref --verify --quiet refs/heads/$LOCAL_BRANCH; then
        echo "🗑️  Deleting local branch $LOCAL_BRANCH..."
        git branch -D $LOCAL_BRANCH
    fi

    # Delete remote branch
    echo "🗑️  Deleting remote branch $branch..."
    git push origin --delete $LOCAL_BRANCH

    echo "✅ Cleaned up $branch"
    echo ""
done

# Push merged changes
echo "📤 Pushing merged changes to $TARGET_BRANCH..."
git push origin $TARGET_BRANCH

echo ""
echo "🎉 All done! Merged and cleaned up all Claude branches into $TARGET_BRANCH"
