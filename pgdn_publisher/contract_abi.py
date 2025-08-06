"""
Contract ABI data embedded in the package to avoid file path issues.
"""

CONTRACT_ABI = [
  {
    "inputs": [],
    "stateMutability": "nonpayable",
    "type": "constructor"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "target",
        "type": "address"
      }
    ],
    "name": "AddressEmptyCode",
    "type": "error"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "implementation",
        "type": "address"
      }
    ],
    "name": "ERC1967InvalidImplementation",
    "type": "error"
  },
  {
    "inputs": [],
    "name": "ERC1967NonPayable",
    "type": "error"
  },
  {
    "inputs": [],
    "name": "EnforcedPause",
    "type": "error"
  },
  {
    "inputs": [],
    "name": "ExpectedPause",
    "type": "error"
  },
  {
    "inputs": [],
    "name": "FailedCall",
    "type": "error"
  },
  {
    "inputs": [],
    "name": "InvalidInitialization",
    "type": "error"
  },
  {
    "inputs": [],
    "name": "NotInitializing",
    "type": "error"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "owner",
        "type": "address"
      }
    ],
    "name": "OwnableInvalidOwner",
    "type": "error"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "account",
        "type": "address"
      }
    ],
    "name": "OwnableUnauthorizedAccount",
    "type": "error"
  },
  {
    "inputs": [],
    "name": "ReentrancyGuardReentrantCall",
    "type": "error"
  },
  {
    "inputs": [],
    "name": "UUPSUnauthorizedCallContext",
    "type": "error"
  },
  {
    "inputs": [
      {
        "internalType": "bytes32",
        "name": "slot",
        "type": "bytes32"
      }
    ],
    "name": "UUPSUnsupportedProxiableUUID",
    "type": "error"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": True,
        "internalType": "address",
        "name": "analyst",
        "type": "address"
      },
      {
        "indexed": False,
        "internalType": "bool",
        "name": "authorized",
        "type": "bool"
      }
    ],
    "name": "AnalystAuthorizationChanged",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "totalHosts",
        "type": "uint256"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "activeHosts",
        "type": "uint256"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "averageScore",
        "type": "uint256"
      },
      {
        "indexed": True,
        "internalType": "address",
        "name": "updater",
        "type": "address"
      }
    ],
    "name": "AnalyticsUpdated",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": True,
        "internalType": "uint256",
        "name": "batchId",
        "type": "uint256"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "scanCount",
        "type": "uint256"
      },
      {
        "indexed": True,
        "internalType": "address",
        "name": "publisher",
        "type": "address"
      }
    ],
    "name": "BatchScansPublished",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": True,
        "internalType": "string",
        "name": "hostUid",
        "type": "string"
      },
      {
        "indexed": False,
        "internalType": "bool",
        "name": "isVerified",
        "type": "bool"
      },
      {
        "indexed": True,
        "internalType": "address",
        "name": "verifier",
        "type": "address"
      }
    ],
    "name": "HostVerificationChanged",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": False,
        "internalType": "uint64",
        "name": "version",
        "type": "uint64"
      }
    ],
    "name": "Initialized",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": True,
        "internalType": "address",
        "name": "moderator",
        "type": "address"
      },
      {
        "indexed": False,
        "internalType": "bool",
        "name": "authorized",
        "type": "bool"
      }
    ],
    "name": "ModeratorAuthorizationChanged",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": True,
        "internalType": "address",
        "name": "previousOwner",
        "type": "address"
      },
      {
        "indexed": True,
        "internalType": "address",
        "name": "newOwner",
        "type": "address"
      }
    ],
    "name": "OwnershipTransferred",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": False,
        "internalType": "address",
        "name": "account",
        "type": "address"
      }
    ],
    "name": "Paused",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": True,
        "internalType": "address",
        "name": "publisher",
        "type": "address"
      },
      {
        "indexed": False,
        "internalType": "bool",
        "name": "authorized",
        "type": "bool"
      }
    ],
    "name": "PublisherAuthorizationChanged",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": True,
        "internalType": "string",
        "name": "hostUid",
        "type": "string"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "oldReputation",
        "type": "uint256"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "newReputation",
        "type": "uint256"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "daysSinceActivity",
        "type": "uint256"
      }
    ],
    "name": "ReputationDecayed",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "oldThreshold",
        "type": "uint256"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "newThreshold",
        "type": "uint256"
      }
    ],
    "name": "ReputationThresholdChanged",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": True,
        "internalType": "string",
        "name": "hostUid",
        "type": "string"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "oldReputation",
        "type": "uint256"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "newReputation",
        "type": "uint256"
      },
      {
        "indexed": False,
        "internalType": "string",
        "name": "reason",
        "type": "string"
      }
    ],
    "name": "ReputationUpdated",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": True,
        "internalType": "bytes32",
        "name": "summaryHash",
        "type": "bytes32"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "deletedAt",
        "type": "uint256"
      },
      {
        "indexed": False,
        "internalType": "string",
        "name": "reason",
        "type": "string"
      },
      {
        "indexed": True,
        "internalType": "address",
        "name": "moderator",
        "type": "address"
      }
    ],
    "name": "ScanDeleted",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": True,
        "internalType": "string",
        "name": "hostUid",
        "type": "string"
      },
      {
        "indexed": True,
        "internalType": "bytes32",
        "name": "summaryHash",
        "type": "bytes32"
      },
      {
        "indexed": False,
        "internalType": "uint16",
        "name": "score",
        "type": "uint16"
      },
      {
        "indexed": False,
        "internalType": "string",
        "name": "reportPointer",
        "type": "string"
      },
      {
        "indexed": True,
        "internalType": "address",
        "name": "publisher",
        "type": "address"
      },
      {
        "indexed": False,
        "internalType": "uint256",
        "name": "reputationAtScan",
        "type": "uint256"
      }
    ],
    "name": "ScanPublished",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": False,
        "internalType": "address",
        "name": "account",
        "type": "address"
      }
    ],
    "name": "Unpaused",
    "type": "event"
  },
  {
    "anonymous": False,
    "inputs": [
      {
        "indexed": True,
        "internalType": "address",
        "name": "implementation",
        "type": "address"
      }
    ],
    "name": "Upgraded",
    "type": "event"
  },
  {
    "inputs": [],
    "name": "UPGRADE_INTERFACE_VERSION",
    "outputs": [
      {
        "internalType": "string",
        "name": "",
        "type": "string"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "VERSION",
    "outputs": [
      {
        "internalType": "string",
        "name": "",
        "type": "string"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "",
        "type": "address"
      }
    ],
    "name": "authorizedPublishers",
    "outputs": [
      {
        "internalType": "bool",
        "name": "",
        "type": "bool"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "getContractInfo",
    "outputs": [
      {
        "internalType": "string",
        "name": "version",
        "type": "string"
      },
      {
        "internalType": "bool",
        "name": "isPaused",
        "type": "bool"
      },
      {
        "internalType": "uint256",
        "name": "totalSummaries",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "publishCooldownPeriod",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "reputationThreshold",
        "type": "uint256"
      },
      {
        "internalType": "uint256",
        "name": "activeHosts",
        "type": "uint256"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [],
    "name": "owner",
    "outputs": [
      {
        "internalType": "address",
        "name": "",
        "type": "address"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [
      {
        "internalType": "string",
        "name": "hostUid",
        "type": "string"
      },
      {
        "internalType": "uint256",
        "name": "scanTime",
        "type": "uint256"
      },
      {
        "internalType": "bytes32",
        "name": "summaryHash",
        "type": "bytes32"
      },
      {
        "internalType": "uint16",
        "name": "score",
        "type": "uint16"
      },
      {
        "internalType": "string",
        "name": "reportPointer",
        "type": "string"
      }
    ],
    "name": "publishScanSummary",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  }
]