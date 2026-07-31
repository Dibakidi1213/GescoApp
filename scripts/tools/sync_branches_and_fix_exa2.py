import sys, os
import argparse
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, db
from models import Course, BulletinBranch


def find_branch_for_course(course):
    # Try exact name match (case-insensitive)
    bp = BulletinBranch.query.filter(BulletinBranch.name.ilike(course.title)).first()
    if bp:
        return bp
    # Try contains
    bp = BulletinBranch.query.filter(BulletinBranch.name.ilike(f"%{course.title}%")).first()
    if bp:
        return bp
    # Fallback: try normalized match by removing accents and lower
    def normalize(s):
        import unicodedata
        if not s:
            return ''
        s = unicodedata.normalize('NFKD', s)
        return ''.join(ch for ch in s if not unicodedata.combining(ch)).lower()

    nt = normalize(course.title)
    for b in BulletinBranch.query.all():
        if normalize(b.name) == nt:
            return b
    return None


def main(dry_run=True, apply_branch_assoc=False, fix_exa2=False):
    with app.app_context():
        # 1) Associate courses to branches when missing (optional)
        assoc_candidates = []
        if apply_branch_assoc:
            courses = Course.query.order_by(Course.id).all()
            for c in courses:
                if c.branch_id:
                    continue
                b = find_branch_for_course(c)
                if b:
                    assoc_candidates.append((c, b))

        # 2) Find branches with max_exam_2 != 20
        bad_branches = BulletinBranch.query.filter(BulletinBranch.max_exam_2 != 20).all()

        print('\nSummary:')
        print(f'  Courses without branch that could be associated: {len(assoc_candidates)}')
        if assoc_candidates and dry_run:
            print('  Example associations (dry-run):')
            for c, b in assoc_candidates[:10]:
                print(f'    Course id={c.id} "{c.title}" -> Branch id={b.id} "{b.name}"')

        print(f'  Branches with max_exam_2 != 20: {len(bad_branches)}')
        if bad_branches and dry_run:
            print('  Example branches (dry-run):')
            for b in bad_branches[:20]:
                print(f'    Branch id={b.id} "{b.name}" max_exam_2={b.max_exam_2}')

        if dry_run:
            print('\nDry-run mode: no changes applied. Run with --apply to persist changes.')
            return 0

        # Apply changes
        if apply_branch_assoc and assoc_candidates:
            for c, b in assoc_candidates:
                print(f'Associating Course id={c.id} "{c.title}" -> Branch id={b.id} "{b.name}"')
                c.branch_id = b.id

        if fix_exa2 and bad_branches:
            for b in bad_branches:
                print(f'Updating Branch id={b.id} "{b.name}" max_exam_2 {b.max_exam_2} -> 20')
                b.max_exam_2 = 20

        db.session.commit()
        print('\nChanges applied.')
        return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sync bulletin branches and fix EXA2 maxima')
    parser.add_argument('--apply', action='store_true', help='Apply the proposed changes')
    parser.add_argument('--assoc-courses', action='store_true', help='Associate courses to branches when missing')
    parser.add_argument('--fix-exa2', action='store_true', help='Set max_exam_2 = 20 for branches that differ')
    args = parser.parse_args()

    exit_code = main(dry_run=not args.apply, apply_branch_assoc=args.assoc_courses, fix_exa2=args.fix_exa2)
    sys.exit(exit_code)
