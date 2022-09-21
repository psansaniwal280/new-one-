

import channels_graphql_ws
import channels
import graphene


class PaymentSubscribe(channels_graphql_ws.Subscription):
    payload = graphene.JSONString()
    paymentIntentId = graphene.String()

    class Arguments:
        paymentIntentId = graphene.String(required=True)

    @staticmethod
    def subscribe(cls, info, **kwargs):
        print("paymentIntentId subscribe --  : ",kwargs.get('paymentIntentId'))
        return [kwargs.get('paymentIntentId')]

    @classmethod
    def publish(payload, info, *args, **kwds):
        print("publishing",payload)
        print("info  ",info)
        return PaymentSubscribe(payload=info, paymentIntentId=kwds.get('paymentIntentId'))


def demo_middleware(next_middleware, root, info, *args, **kwds):
    if info.operation.name is not None and info.operation.name.value != "IntrospectionQuery":
        print("Demo middleware report")
        print("operation:",info.operation.operation)
        print("name:",info.operation.name.value)
    return next_middleware(root, info, *args, **kwds)


class Subscription(graphene.ObjectType):
    paymentSubscribe = PaymentSubscribe.Field()
