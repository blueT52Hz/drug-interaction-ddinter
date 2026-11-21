from app.knowledge.models import Severity
from app.services.interaction_service import check_interactions


def test_major_pair_found_in_either_order(knowledge_base):
    result = check_interactions(knowledge_base, ["REG-ASPIRIN", "REG-WARFARIN"])

    assert result.hasMajor is True
    assert len(result.interactions) == 1
    pair = result.interactions[0]
    assert pair.id == "ddi:DD1:DD2"
    assert pair.severity == Severity.MAJOR
    # drug1 là thuốc gửi lên trước
    assert pair.drug1.registrationNumber == "REG-ASPIRIN"
    assert pair.ingredient1 == "Aspirin"
    assert pair.management == "Avoid combination."


def test_pairs_sorted_most_severe_first(knowledge_base):
    result = check_interactions(knowledge_base, ["REG-PARA", "REG-WARFARIN", "REG-ASPIRIN"])

    assert [pair.severity for pair in result.interactions] == [Severity.MAJOR, Severity.MODERATE]


def test_no_interaction_means_no_major(knowledge_base):
    result = check_interactions(knowledge_base, ["REG-PARA", "REG-ASPIRIN"])

    assert result.interactions == []
    assert result.hasMajor is False


def test_unknown_level_is_returned_but_not_major(knowledge_base):
    result = check_interactions(knowledge_base, ["REG-PARA-CAF", "REG-ASPIRIN"])

    assert [pair.severity for pair in result.interactions] == [Severity.UNKNOWN]
    assert result.hasMajor is False


def test_duplicate_ingredient(knowledge_base):
    result = check_interactions(knowledge_base, ["REG-PARA", "REG-PARA-CAF"])

    assert len(result.duplicates) == 1
    duplicate = result.duplicates[0]
    assert duplicate.id == "dup:DD3"
    assert duplicate.ingredient == "Acetaminophen"
    assert [d.registrationNumber for d in duplicate.drugs] == ["REG-PARA", "REG-PARA-CAF"]
    # cùng hoạt chất thì không báo thành cặp tương tác
    assert result.interactions == []


def test_same_drug_sent_twice_is_ignored(knowledge_base):
    result = check_interactions(knowledge_base, ["REG-PARA", "REG-PARA"])

    assert result.duplicates == []
    assert result.interactions == []


def test_not_found_and_incomplete_drugs_are_reported(knowledge_base):
    result = check_interactions(knowledge_base, ["REG-WARFARIN", "NOPE", "REG-PARTIAL", "REG-EMPTY"])

    assert result.notFound == ["NOPE"]
    assert result.incomplete == ["REG-PARTIAL", "REG-EMPTY"]
    # Phần đã map của thuốc nửa map vẫn được kiểm tra
    assert result.hasMajor is True
