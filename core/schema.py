import graphene
import channels_graphql_ws

from app.schemas.badgesSchema import badgesQuery, badgesMutation
from app.schemas.directMessagingSchema import directMessagingQuery, directMessagingMutation
from app.schemas.paymentsSchema.paymentSubscription import demo_middleware, Subscription
from app.schemas.postSchema import postQuery, postMutation
from app.schemas.userSchema import userQuery, userMutation
from app.schemas.exploreSchema import exploreQuery, exploreMutation
from app.schemas.feedSchema import feedQuery, feedMutation
from app.schemas.itinerarySchema import itineraryQuery, itineraryMutation
from app.schemas.paymentsSchema import paymentsQuery, paymentsMutation
from app.schemas.reportSchema import reportQuery, reportMutation
from app.schemas.searchSchema import searchQuery, searchMutation
from app.schemas.userAccountSchema import userAccountQuery, userAccountMutation
from app.schemas.vendorSchema import vendorQuery, vendorMutation
from app.schemas.venueSchema import venueQuery, venueMutation
from app.schemas.userTravelSchema import userTravelQuery, userTravelMutation


class Query(badgesQuery.Query, postQuery.Query, directMessagingQuery.Query, userQuery.Query, exploreQuery.Query,
            feedQuery.Query, itineraryQuery.Query, paymentsQuery.Query, reportQuery.Query,
            searchQuery.Query, userAccountQuery.Query, vendorQuery.Query, venueQuery.Query, userTravelQuery.Query, graphene.ObjectType):
    pass


class Mutation(badgesMutation.Mutation, postMutation.Mutation, directMessagingMutation.Mutation, userMutation.Mutation,
               exploreMutation.Mutation, feedMutation.Mutation, itineraryMutation.Mutation, paymentsMutation.Mutation, reportMutation.Mutation,
               searchMutation.Mutation, userAccountMutation.Mutation, vendorMutation.Mutation, venueMutation.Mutation, userTravelMutation.Mutation, graphene.ObjectType):
    pass


# class Query(app.schema.Query, graphene.ObjectType):
#     pass
# class Mutation(app.schema.Mutation, graphene.ObjectType):
#     pass

schema = graphene.Schema(query=Query, mutation=Mutation, subscription=Subscription)


class MyGraphqlWsConsumer(channels_graphql_ws.GraphqlWsConsumer):
    """Channels WebSocket consumer which provides GraphQL API."""
    schema = schema
    middleware = [demo_middleware]

    async def on_connect(self, payload):
        """New client connection handler."""
        # You can `raise` from here to reject the connection.
        print("New client connected!")

    async def disconnect(self, code):
        print("New client Disconnected!")
