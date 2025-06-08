import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db, Vote, Voter, Nominee

def reset_votes():
    with app.app_context():
        print("🗳️  Resetting All Votes")
        print("-" * 30)
        
        confirm = input("This will delete ALL votes and reset voter status. Are you sure? (yes/no): ")
        if confirm.lower() != 'yes':
            print("❌ Operation cancelled")
            return
        
        # Delete all votes
        vote_count = Vote.query.count()
        Vote.query.delete()
        
        # Reset voter status
        voters = Voter.query.all()
        for voter in voters:
            voter.has_voted = False
        
        # Reset nominee vote counts
        nominees = Nominee.query.all()
        for nominee in nominees:
            nominee.vote_count = 0
        
        db.session.commit()
        
        print(f"✅ Deleted {vote_count} votes")
        print(f"✅ Reset {len(voters)} voter statuses")
        print(f"✅ Reset {len(nominees)} nominee vote counts")
        print("🎉 Voting system is ready for a fresh election!")

if __name__ == '__main__':
    reset_votes()
