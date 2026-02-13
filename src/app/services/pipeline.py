from datetime import datetime, timedelta

from beanie import PydanticObjectId


class MongoPipelineBuilder:
    """Builds aggregation pipelines."""

    @staticmethod
    def build_dashboard_pipeline(user_id: str, today: datetime) -> list:
        """Build dashboard pipeline."""
        week_limit = today + timedelta(days=7)

        return [
            {'$match': {'user_id': PydanticObjectId(user_id)}},
            {
                '$facet': {
                    'total': [{'$count': 'value'}],
                    'attention': [
                        {
                            '$match': {
                                '$or': [
                                    {'next_watering_at': {'$lte': today}},
                                    {'next_fertilizing_at': {'$lte': today}},
                                ]
                            }
                        },
                        {'$count': 'value'},
                    ],
                    'watering_week': [
                        {
                            '$match': {
                                'next_watering_at': {
                                    '$gte': today,
                                    '$lte': week_limit,
                                }
                            }
                        },
                        {'$count': 'value'},
                    ],
                    'tasks': [
                        {'$match': {'next_watering_at': {'$ne': None}}},
                        {'$sort': {'next_watering_at': 1}},
                        {'$limit': 10},
                        {
                            '$project': {
                                'plant_id': '$_id',
                                'name': 1,
                                'date': '$next_watering_at',
                                'type': {
                                    '$cond': [
                                        {
                                            '$eq': [
                                                '$next_watering_at',
                                                '$next_fertilizing_at',
                                            ]
                                        },
                                        'watering_with_fertilizing',
                                        'watering',
                                    ]
                                },
                            }
                        },
                    ],
                }
            },
        ]
