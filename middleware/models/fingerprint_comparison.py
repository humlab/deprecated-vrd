from video_reuse_detector.fingerprint import FingerprintComparison, MatchLevel

from . import db, ma


class FingerprintComparisonModel(db.Model):  # type: ignore
    __tablename__ = 'fingerprint_comparisons'

    pk = db.Column(db.Integer(), primary_key=True)

    query_video_name = db.Column(db.String())
    reference_video_name = db.Column(db.String())
    query_segment_id = db.Column(db.Integer())
    reference_segment_id = db.Column(db.Integer())
    match_level = db.Column(db.String())
    similarity_score = db.Column(db.Float())

    similar_enough_th = db.Column(db.Boolean())
    could_compare_cc = db.Column(db.Boolean())
    similar_enough_cc = db.Column(db.Boolean())
    could_compare_orb = db.Column(db.Boolean())
    similar_enough_orb = db.Column(db.Boolean())

    __table_args__ = (
        db.UniqueConstraint(
            'query_video_name',
            'reference_video_name',
            'query_segment_id',
            'reference_segment_id',
        ),
    )

    def to_fingerprint_comparison(self) -> FingerprintComparison:
        return FingerprintComparison(
            self.query_video_name,
            self.reference_video_name,
            self.query_segment_id,
            self.reference_segment_id,
            MatchLevel[self.match_level],
            self.similarity_score,
            self.similar_enough_th,
            self.could_compare_cc,
            self.similar_enough_cc,
            self.could_compare_orb,
            self.similar_enough_orb,
        )

    @staticmethod
    def from_fingerprint_comparison(fc: FingerprintComparison):
        return FingerprintComparisonModel(
            query_video_name=fc.query_video_name,
            reference_video_name=fc.reference_video_name,
            query_segment_id=fc.query_segment_id,
            reference_segment_id=fc.reference_segment_id,
            match_level=str(fc.match_level),
            similarity_score=fc.similarity_score,
            similar_enough_th=fc.similar_enough_th,
            could_compare_cc=fc.could_compare_cc,
            similar_enough_cc=fc.similar_enough_cc,
            could_compare_orb=fc.could_compare_orb,
            similar_enough_orb=fc.could_compare_orb,
        )


class FingerprintComparisonSchema(ma.ModelSchema):
    class Meta:
        model = FingerprintComparisonModel
