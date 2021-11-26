
from brownie import Lottery, accounts, config, network, exceptions
from web3 import Web3 
from scripts.deploy_lottery import deploy_lottery
from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS, get_account, fund_with_link, get_contract
import pytest
import time

#def test_get_entrance_fee():
#    account = accounts[0]
#    lottery = Lottery.deploy(
#        config["networks"][network.show_active()]["eth_usd_price_feed"], 
#        {"from": account},
#        )
#    assert lottery.getEntranceFee() > Web3.toWei(0.010, "ether")
    #assert lottery.getEntranceFee() < Web3.toWei(0.050, "ether")

def test_get_entrance_fee():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    # Arrange
    lottery = deploy_lottery()
    # Act
    # 2,000 eth/usd
    # usdEntreFee is 50 
    expected_entrance_fee = Web3.toWei(0.025,"ether") 
    entrance_fee = lottery.getEntranceFee()
    # Assert
    assert expected_entrance_fee == entrance_fee

def test_cant_enter_unless_started():
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    with pytest.raises(exceptions.VirtualMachineError):
        lottery.enter({"from": get_account(), "value": lottery.getEntranceFee()})

def test_can_start_and_enter_lottery():
    # arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()
    account = get_account()
    lottery.startLottery({"from":account})
    # Act
    lottery.enter({"from":account, "value": lottery.getEntranceFee()})
    # Assert 
    assert lottery.players(0)

def test_can_end_lottery(): 
    # arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()    
    account = get_account()
    lottery.startLottery({"from": account})
    time.sleep(1)
    # Act
    lottery.enter({"from":account, "value": lottery.getEntranceFee()})
    time.sleep(1)
    fund_with_link(lottery)
    time.sleep(1)
    lottery.endLottery({"from": account})
    time.sleep(1)
    assert lottery.lottery_state() == 2

def test_can_pick_winner_correctly():
    # arrange
    if network.show_active() not in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        pytest.skip()
    lottery = deploy_lottery()    
    account = get_account()
    lottery.startLottery({"from": account})    
    # Act
    lottery.enter({"from":account, "value": lottery.getEntranceFee()})
    lottery.enter({"from":get_account(index=1), "value": lottery.getEntranceFee()})
    lottery.enter({"from":get_account(index=2), "value": lottery.getEntranceFee()})
    fund_with_link(lottery)
    time.sleep(1)
    starting_balance_of_account = account.balance()
    balance_of_lottery = lottery.balance()
    transaction = lottery.endLottery({"from": account})
    requestId = transaction.events["RequestedRandomness"]["requestId"]
    STATIC_RNG = 777
    get_contract("vrf_coordinator").callBackWithRandomness(requestId, STATIC_RNG, lottery.address, {"from": account})
    # 777 % 3 
    assert lottery.recentWinner() == account
    assert lottery.balance() == 0
    assert account.balance() == starting_balance_of_account + balance_of_lottery
