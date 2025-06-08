import sys
import os
import random
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db, Vote, Voter, Nominee, Position

def add_sample_votes():
    with app.app_context():
        print("🎯 Adding Sample Votes")
        print("-" * 30)
        
        voters = Voter.query.all()
        positions = Position.query.all()
        
        if not voters:
            print("❌ No voters found! Please add voters first.")
            return
        
        if not positions:
            print("❌ No positions found! Please add positions first.")
            return
        
        vote_count = 0
        
        # Simulate votes for each voter
        for voter in voters[:100]:  # Limit to first 100 voters for demo
            if voter.has_voted:
                continue
                
            # Vote for each position
            for position in positions:
                nominees = Nominee.query.filter_by(position_id=position.id).all()
                if nominees:
                    # Randomly select a nominee (weighted towards first nominees for demo)
                    weights = [3, 2, 1, 1][:len(nominees)]
                    selected_nominee = random.choices(nominees, weights=weights)[0]
                    
                    # Create vote
                    vote = Vote(
                        voter_id=voter.id,
                        nominee_id=selected_nominee.id,
                        position_id=position.id
                    )
                    db.session.add(vote)
                    
                    # Update nominee vote count
                    selected_nominee.vote_count += 1
                    vote_count += 1
            
            # Mark voter as having voted
            voter.has_voted = True
        
        db.session.commit()
        
        print(f"✅ Added {vote_count} sample votes")
        print(f"✅ Marked {len([v for v in voters if v.has_voted])} voters as having voted")
        print("🎉 Sample voting data created!")

if __name__ == '__main__':
    add_sample_votes()
