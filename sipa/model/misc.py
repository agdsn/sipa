from collections import namedtuple


TransactionTuple = namedtuple('Transaction', ['datum', 'value'])

PaymentDetails = namedtuple('PaymentDetails', 'recipient bank iban bic purpose')
