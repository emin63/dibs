import string

# version number = major_version.minor_version sub_minor_version
# For example, if the following variables are 0, 9, 1 then the
# resulting version number is 0.91
major_version = 0
minor_version = 9
sub_minor_version = 3
version_string = `major_version` + '.' + `minor_version` + `sub_minor_version`


forgetYouCmdName = 'FORGET_YOU'
clearCmdName = 'CLEAR_DB'
storeCmdName = 'STORE'
unstoreCmdName = 'UNSTORE'
recoverCmdName = 'RECOVER'
recoverAllCmdName = 'RECOVER_ALL'
doneRecoverAllCmdName = 'FINISHED_RECOVER_ALL'
recoverResponseCmdName = 'RECOVER_RESPONSE'
probeCmdName = 'PROBE'
probeResponseCmdName = 'PROBE_RESPONSE'
proposalCmdName = 'PEER_CONTRACT_PROPOSAL'
proposalResponseCmdName = 'PEER_CONTRACT_RESPONSE'
proposalDecisionArgName = 'CONTRACT_DECISION'
proposalCommentArgName = 'PROPOSAL_COMMENT'

dibsCmdNames = [storeCmdName, unstoreCmdName, recoverCmdName, probeCmdName,
                recoverResponseCmdName, clearCmdName, forgetYouCmdName,
                recoverAllCmdName, doneRecoverAllCmdName,
                probeResponseCmdName, proposalCmdName]

cmdTagName = 'COMMAND'
argTagName = 'ARGUMENT'

pieceNameArgName = 'PIECE_NAME'
pieceDataArgName = 'PAYLOAD'
cmdTimeArgName = 'CMD_TIME'
contractNameArgName = 'CONTRACT_NAME'
publicKeyNameArgName = 'PUB_KEY_NAME'
publicKeyArgName = 'PUB_KEY'
adminArgName = 'DIBS_ADMIN'
talkTypeArgName = 'TALK'
listenTypeArgName = 'LISTEN'
remoteQuotaArgName = 'REMOTE_QUOTA'
localQuotaArgName = 'LOCAL_QUOTA'
hostArgName = 'HOST'
portArgName = 'PORT'

proposalErrors = { 'unknown_contract' : 'unknown_contract',
                   'remote_quota_range' : 'remote_quota_range',
                   'bad_quota_mult' : 'bad_quota_mult',
                   'bad_talk_type' : 'bad_talk_type',
                   'exception' : 'exception' }

adminField = 'DIBS-ADMIN:'
dibsToField = 'DIBS-To:'
sendmailCommand = '/usr/sbin/sendmail'

pgpMsgStart = '-----BEGIN PGP MESSAGE-----\n'
pgpMsgEnd = '\n-----END PGP MESSAGE-----\n'

pgpKeyStart = '-----BEGIN PGP PUBLIC KEY BLOCK-----\n'
pgpKeyEnd = '\n-----END PGP PUBLIC KEY BLOCK-----\n'

daemonCmdSize = 256

talkMethods = ['active','passive','smtplib','sendmail']
defaultPort = 6363

# The following pattern is used by dibs to store various files.
# It should not exist in files the user asks dibs to store.
# Make sure the pattern doesn't contain any characters which
# have special meanings in regular expressions (e.g. *, +, ., ?, etc.)
fileSeparator = '@@DIBS@@'

# If the pattern named by fileSeparator is present, a warning
# will be gnerated and it will be replaced by the following pattern.
transSep = '##DIBS##'

# When we are storing files for peers, we have a directory tree
# like a/b/c/.../<fileName> and this variable controls how many
# levels we have in that tree.
storageDirDepth = 3

