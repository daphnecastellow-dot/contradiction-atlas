import tempfile
import unittest
from pathlib import Path
from contradiction_atlas import AtlasError, add_claim, add_conflict, add_source, change_status, load, new_project, render_markdown, render_matrix, render_mermaid, save

class ContradictionAtlasTests(unittest.TestCase):
    def test_conflict_stays_open_by_default(self):
        d=new_project("Test Atlas")
        s1=add_source(d,"Logbook","primary","1901")
        s2=add_source(d,"Newspaper","contemporary-report","1901-03-02")
        c1=add_claim(d,"The bell rang three times.",[s1])
        c2=add_claim(d,"The bell rang twice.",[s2])
        x=add_conflict(d,c1,c2,"count")
        self.assertEqual(x,"X001")
        self.assertEqual(d["conflicts"][0]["status"],"open")

    def test_status_change_preserves_history(self):
        d=new_project("History")
        c1=add_claim(d,"The event occurred before midnight.")
        c2=add_claim(d,"The event occurred after midnight.")
        x=add_conflict(d,c1,c2,"time","Records disagree.")
        change_status(d,x,"narrowed","Both accounts place the event within a ten-minute window.","The practical range is smaller.")
        self.assertEqual(d["conflicts"][0]["status"],"narrowed")
        self.assertEqual(d["conflicts"][0]["history"][1]["previous_status"],"open")

    def test_rejects_self_and_duplicate_pair_conflicts(self):
        d=new_project("Bad"); c1=add_claim(d,"One"); c2=add_claim(d,"Two")
        with self.assertRaises(AtlasError): add_conflict(d,c1,c1,"other")
        add_conflict(d,c1,c2,"wording")
        with self.assertRaises(AtlasError): add_conflict(d,c2,c1,"interpretation")

    def test_round_trip_and_renderers(self):
        d=new_project("Render"); c1=add_claim(d,"A"); c2=add_claim(d,"B"); add_conflict(d,c1,c2,"identity")
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"atlas.json"; save(p,d); d=load(p)
        self.assertIn("X001 · identity · open",render_markdown(d))
        self.assertIn("X001 · open",render_matrix(d))
        self.assertIn('C001 <-->|"X001 · identity · open"| C002',render_mermaid(d))

if __name__=="__main__": unittest.main()
